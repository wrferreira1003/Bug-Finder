import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

import google.generativeai as genai

from ..models import (
    LogModel, ProcessedLog, BugAnalysis, AnalysisResult, 
    BugSeverity, BugCategory, BugImpact, AnalysisDecision, LogLevel
)
from ..config import get_settings, get_prompt


class BugAnalyserAgent:
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Configure Google AI
        genai.configure(api_key=self.settings.google_ai_api_key)
        self.model = genai.GenerativeModel(self.settings.gemini_model)
        
        # Generation config
        self.generation_config = {
            "temperature": self.settings.gemini_temperature,
            "max_output_tokens": self.settings.gemini_max_tokens,
        }
    
    def process_and_analyze_log(self, raw_log: str) -> AnalysisResult:
        """
        Processa o log bruto e realiza análise completa para determinar se é um bug.
        Combina as funcionalidades de LogReceiver + BugAnalyser em um só agente.
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting log processing and analysis")
            
            # Etapa 1: Processar log bruto
            processed_log = self._process_raw_log(raw_log)
            
            if not processed_log.is_valid:
                self.logger.warning("Log processing failed, creating minimal analysis")
                return self._create_failed_analysis(raw_log, processed_log, start_time)
            
            # Etapa 2: Analisar se é bug
            bug_analysis = self._analyze_bug(processed_log)
            
            # Criar resultado final
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = AnalysisResult(
                log=processed_log.parsed_log,
                analysis=bug_analysis,
                processing_time_ms=processing_time,
                analyzer_version="1.0.0"
            )
            
            self.logger.info(f"Analysis completed - Bug: {bug_analysis.is_bug}, "
                           f"Severity: {bug_analysis.severity}, Decision: {bug_analysis.decision}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in log analysis: {str(e)}")
            return self._create_error_analysis(raw_log, str(e), start_time)
    
    def _process_raw_log(self, raw_log: str) -> ProcessedLog:
        """Processa o log bruto e extrai informações estruturadas."""
        try:
            # Prompt para processamento de log
            prompt = get_prompt("log_receiver", raw_log=raw_log)
            
            self.logger.debug("Sending log processing request to AI")
            response = self.model.generate_content(
                prompt, 
                generation_config=self.generation_config
            )
            
            # Parse da resposta JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            # Criar LogModel a partir do resultado
            if result.get("is_valid", False) and "parsed_log" in result:
                parsed_data = result["parsed_log"]
                
                # Converter timestamp string para datetime se necessário
                if isinstance(parsed_data.get("timestamp"), str):
                    try:
                        parsed_data["timestamp"] = datetime.fromisoformat(parsed_data["timestamp"])
                    except:
                        parsed_data["timestamp"] = datetime.now()
                elif not parsed_data.get("timestamp"):
                    parsed_data["timestamp"] = datetime.now()
                
                # Garantir que level seja válido
                level = parsed_data.get("level", "ERROR")
                if level not in [e.value for e in LogLevel]:
                    level = "ERROR"
                parsed_data["level"] = level
                
                log_model = LogModel(**parsed_data)
                
                return ProcessedLog(
                    raw_log=raw_log,
                    parsed_log=log_model,
                    is_valid=True,
                    validation_errors=result.get("validation_errors", [])
                )
            else:
                # Log inválido ou mal formatado
                return ProcessedLog(
                    raw_log=raw_log,
                    parsed_log=self._create_fallback_log(raw_log),
                    is_valid=False,
                    validation_errors=result.get("validation_errors", ["Failed to parse log"])
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            return ProcessedLog(
                raw_log=raw_log,
                parsed_log=self._create_fallback_log(raw_log),
                is_valid=False,
                validation_errors=[f"JSON parse error: {str(e)}"]
            )
        except Exception as e:
            self.logger.error(f"Error processing log: {e}")
            return ProcessedLog(
                raw_log=raw_log,
                parsed_log=self._create_fallback_log(raw_log),
                is_valid=False,
                validation_errors=[f"Processing error: {str(e)}"]
            )
    
    def _analyze_bug(self, processed_log: ProcessedLog) -> BugAnalysis:
        """Analisa se o log processado representa um bug real."""
        try:
            # Preparar contexto do log para análise
            log_context = {
                "timestamp": processed_log.parsed_log.timestamp.isoformat(),
                "level": processed_log.parsed_log.level,
                "message": processed_log.parsed_log.message,
                "source": processed_log.parsed_log.source,
                "function_name": processed_log.parsed_log.function_name,
                "stack_trace": processed_log.parsed_log.stack_trace,
                "additional_data": processed_log.parsed_log.additional_data
            }
            
            # Prompt para análise de bug
            prompt = get_prompt("bug_analyser", log_context=json.dumps(log_context, indent=2))
            
            self.logger.debug("Sending bug analysis request to AI")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse da resposta JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            result = json.loads(response_text)
            
            # Criar BugAnalysis
            analysis = BugAnalysis(
                log_id=str(uuid4()),
                is_bug=result.get("is_bug", False),
                severity=BugSeverity(result.get("severity", "low")),
                category=BugCategory(result.get("category", "other")),
                impact=BugImpact(result.get("impact", "low_impact")),
                decision=AnalysisDecision(result.get("decision", "ignore")),
                root_cause_hypothesis=result.get("root_cause_hypothesis"),
                affected_components=result.get("affected_components", []),
                reproduction_likelihood=result.get("reproduction_likelihood", 0.0),
                priority_score=result.get("priority_score", 0.0),
                confidence_score=result.get("confidence_score", 0.0),
                analysis_notes=result.get("analysis_notes")
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse analysis response as JSON: {e}")
            return self._create_fallback_analysis()
        except Exception as e:
            self.logger.error(f"Error in bug analysis: {e}")
            return self._create_fallback_analysis()
    
    def _create_fallback_log(self, raw_log: str) -> LogModel:
        """Cria um LogModel básico quando o processamento falha."""
        return LogModel(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            message=raw_log[:500] if len(raw_log) > 500 else raw_log,
            source="unknown",
            additional_data={"raw_input": raw_log}
        )
    
    def _create_fallback_analysis(self) -> BugAnalysis:
        """Cria uma análise básica quando a análise AI falha."""
        return BugAnalysis(
            log_id=str(uuid4()),
            is_bug=False,
            severity=BugSeverity.LOW,
            category=BugCategory.OTHER,
            impact=BugImpact.LOW_IMPACT,
            decision=AnalysisDecision.IGNORE,
            confidence_score=0.0,
            priority_score=0.0,
            analysis_notes="Analysis failed, created fallback"
        )
    
    def _create_failed_analysis(self, raw_log: str, processed_log: ProcessedLog, start_time: datetime) -> AnalysisResult:
        """Cria um resultado de análise para logs que falharam no processamento."""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        analysis = BugAnalysis(
            log_id=str(uuid4()),
            is_bug=False,
            severity=BugSeverity.LOW,
            category=BugCategory.OTHER,
            impact=BugImpact.LOW_IMPACT,
            decision=AnalysisDecision.IGNORE,
            confidence_score=0.0,
            priority_score=0.0,
            analysis_notes=f"Log processing failed: {', '.join(processed_log.validation_errors or [])}"
        )
        
        return AnalysisResult(
            log=processed_log.parsed_log,
            analysis=analysis,
            processing_time_ms=processing_time,
            analyzer_version="1.0.0"
        )
    
    def _create_error_analysis(self, raw_log: str, error_message: str, start_time: datetime) -> AnalysisResult:
        """Cria um resultado de análise para erros inesperados."""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        fallback_log = self._create_fallback_log(raw_log)
        analysis = BugAnalysis(
            log_id=str(uuid4()),
            is_bug=False,
            severity=BugSeverity.LOW,
            category=BugCategory.OTHER,
            impact=BugImpact.LOW_IMPACT,
            decision=AnalysisDecision.IGNORE,
            confidence_score=0.0,
            priority_score=0.0,
            analysis_notes=f"Analysis error: {error_message}"
        )
        
        return AnalysisResult(
            log=fallback_log,
            analysis=analysis,
            processing_time_ms=processing_time,
            analyzer_version="1.0.0"
        )