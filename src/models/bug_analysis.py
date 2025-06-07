"""
Modelo que representa a análise de um bug feita pelo agente analisador.

Este modelo padroniza o resultado da análise inteligente que determina
se um log representa realmente um bug e qual sua importância.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class BugSeverity(Enum):
    """
    Níveis de severidade de um bug.
    
    Define quão crítico é o problema encontrado.
    """
    LOW = "low"          # Bug menor, não afeta funcionalidade principal
    MEDIUM = "medium"    # Bug importante, afeta funcionalidade mas não crítica
    HIGH = "high"        # Bug sério, afeta funcionalidade crítica
    CRITICAL = "critical" # Bug crítico, sistema pode parar de funcionar

class BugCategory(Enum):
    """
    Categorias de bugs para classificação.
    
    Ajuda a organizar e priorizar os diferentes tipos de problemas.
    """
    AUTHENTICATION = "authentication"     # Problemas de login/autenticação
    DATABASE = "database"                 # Erros de banco de dados
    API = "api"                          # Problemas em APIs
    FRONTEND = "frontend"                # Erros de interface
    BACKEND = "backend"                  # Problemas no servidor
    NETWORK = "network"                  # Problemas de conectividade
    SECURITY = "security"                # Problemas de segurança
    PERFORMANCE = "performance"          # Problemas de performance
    DATA_INTEGRITY = "data_integrity"    # Problemas com dados
    THIRD_PARTY = "third_party"          # Problemas com serviços externos
    UNKNOWN = "unknown"                  # Categoria não identificada

@dataclass
class BugAnalysis:
    """
    Representa a análise completa de um bug feita pela IA.
    
    Esta classe contém toda a informação que o agente analisador
    conseguiu extrair e determinar sobre um log de erro.
    
    Attributes:
        is_bug (bool): Se o log representa realmente um bug
        confidence (float): Confiança da IA na análise (0.0 a 1.0)
        severity (BugSeverity): Quão crítico é o bug
        category (BugCategory): Categoria do problema
        title (str): Título sugerido para a issue
        description (str): Descrição detalhada do problema
        impact_description (str): Descrição do impacto nos usuários
        suggested_priority (str): Prioridade sugerida (P0, P1, P2, P3)
        affected_components (List[str]): Componentes do sistema afetados
        possible_causes (List[str]): Possíveis causas do problema
        suggested_tags (List[str]): Tags sugeridas para a issue
        estimated_users_affected (Optional[int]): Estimativa de usuários afetados
        business_impact (Optional[str]): Impacto no negócio
        urgency_reason (Optional[str]): Por que é urgente (se for)
        similar_issues_found (List[str]): Links para issues similares
        analysis_timestamp (datetime): Quando a análise foi feita
        analysis_metadata (Dict[str, Any]): Metadados da análise
    """
    
    # Resultado principal da análise
    is_bug: bool
    confidence: float
    
    # Classificação do bug (se for um bug)
    severity: Optional[BugSeverity] = None
    category: Optional[BugCategory] = None
    
    # Informações para criação da issue
    title: Optional[str] = None
    description: Optional[str] = None
    impact_description: Optional[str] = None
    suggested_priority: Optional[str] = None
    
    # Detalhes técnicos
    affected_components: Optional[List[str]] = None
    possible_causes: Optional[List[str]] = None
    suggested_tags: Optional[List[str]] = None
    
    # Análise de impacto
    estimated_users_affected: Optional[int] = None
    business_impact: Optional[str] = None
    urgency_reason: Optional[str] = None
    
    # Contexto adicional
    similar_issues_found: Optional[List[str]] = None
    
    # Metadados
    analysis_timestamp: Optional[datetime] = None
    analysis_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """
        Validações e ajustes após criação do objeto.
        """
        # Define timestamp se não foi fornecido
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
        
        # Inicializa listas vazias se None
        if self.affected_components is None:
            self.affected_components = []
        if self.possible_causes is None:
            self.possible_causes = []
        if self.suggested_tags is None:
            self.suggested_tags = []
        if self.similar_issues_found is None:
            self.similar_issues_found = []
        if self.analysis_metadata is None:
            self.analysis_metadata = {}
        
        # Validações
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar entre 0.0 e 1.0")
        
        # Se é um bug, alguns campos são obrigatórios
        if self.is_bug:
            if self.severity is None:
                raise ValueError("severity é obrigatório quando is_bug=True")
            if self.category is None:
                self.category = BugCategory.UNKNOWN
    
    @property
    def is_critical_bug(self) -> bool:
        """
        Verifica se é um bug crítico que precisa atenção imediata.
        
        Returns:
            bool: True se é um bug crítico
        """
        return (self.is_bug and 
                self.severity == BugSeverity.CRITICAL and 
                self.confidence >= 0.7)
    
    @property
    def should_create_issue(self) -> bool:
        """
        Determina se uma issue deve ser criada baseada na análise.
        
        Returns:
            bool: True se deve criar issue
        """
        # Só cria issue se:
        # 1. É realmente um bug
        # 2. Confiança é alta (>= 0.6)
        # 3. Severidade é pelo menos MEDIUM
        return (self.is_bug and 
                self.confidence >= 0.6 and 
                self.severity in [BugSeverity.MEDIUM, BugSeverity.HIGH, BugSeverity.CRITICAL])
    
    @property
    def confidence_level(self) -> str:
        """
        Retorna o nível de confiança em formato texto.
        
        Returns:
            str: Nível de confiança (baixa, média, alta)
        """
        if self.confidence >= 0.8:
            return "alta"
        elif self.confidence >= 0.6:
            return "média"
        else:
            return "baixa"
    
    def get_priority_score(self) -> int:
        """
        Calcula um score de prioridade baseado na análise.
        
        Returns:
            int: Score de 0 (baixa prioridade) a 100 (altíssima prioridade)
        """
        if not self.is_bug:
            return 0
        
        # Score base por severidade
        severity_scores = {
            BugSeverity.LOW: 10,
            BugSeverity.MEDIUM: 30,
            BugSeverity.HIGH: 60,
            BugSeverity.CRITICAL: 90
        }
        
        base_score = severity_scores.get(self.severity, 0)
        
        # Multiplicador por confiança
        confidence_multiplier = self.confidence
        
        # Bônus por usuários afetados
        users_bonus = 0
        if self.estimated_users_affected:
            if self.estimated_users_affected > 1000:
                users_bonus = 10
            elif self.estimated_users_affected > 100:
                users_bonus = 5
        
        # Bônus por urgência
        urgency_bonus = 10 if self.urgency_reason else 0
        
        final_score = int((base_score * confidence_multiplier) + users_bonus + urgency_bonus)
        return min(final_score, 100)  # Cap em 100
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a análise para dicionário.
        
        Returns:
            Dict[str, Any]: Representação em dicionário
        """
        return {
            'is_bug': self.is_bug,
            'confidence': self.confidence,
            'severity': self.severity.value if self.severity else None,
            'category': self.category.value if self.category else None,
            'title': self.title,
            'description': self.description,
            'impact_description': self.impact_description,
            'suggested_priority': self.suggested_priority,
            'affected_components': self.affected_components,
            'possible_causes': self.possible_causes,
            'suggested_tags': self.suggested_tags,
            'estimated_users_affected': self.estimated_users_affected,
            'business_impact': self.business_impact,
            'urgency_reason': self.urgency_reason,
            'similar_issues_found': self.similar_issues_found,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'analysis_metadata': self.analysis_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BugAnalysis':
        """
        Cria uma BugAnalysis a partir de dicionário.
        
        Args:
            data (Dict[str, Any]): Dados da análise
            
        Returns:
            BugAnalysis: Nova instância
        """
        return cls(
            is_bug=data['is_bug'],
            confidence=data['confidence'],
            severity=BugSeverity(data['severity']) if data.get('severity') else None,
            category=BugCategory(data['category']) if data.get('category') else None,
            title=data.get('title'),
            description=data.get('description'),
            impact_description=data.get('impact_description'),
            suggested_priority=data.get('suggested_priority'),
            affected_components=data.get('affected_components', []),
            possible_causes=data.get('possible_causes', []),
            suggested_tags=data.get('suggested_tags', []),
            estimated_users_affected=data.get('estimated_users_affected'),
            business_impact=data.get('business_impact'),
            urgency_reason=data.get('urgency_reason'),
            similar_issues_found=data.get('similar_issues_found', []),
            analysis_timestamp=datetime.fromisoformat(data['analysis_timestamp']) if data.get('analysis_timestamp') else None,
            analysis_metadata=data.get('analysis_metadata', {})
        )
    
    def __str__(self) -> str:
        """
        Representação em string da análise.
        """
        status = "BUG" if self.is_bug else "NÃO É BUG"
        severity = f" ({self.severity.value.upper()})" if self.severity else ""
        confidence = f" - Confiança: {self.confidence:.1%}"
        
        return f"BugAnalysis: {status}{severity}{confidence}"
    
    def __repr__(self) -> str:
        """
        Representação técnica da análise.
        """
        return (f"BugAnalysis(is_bug={self.is_bug}, confidence={self.confidence}, "
                f"severity={self.severity}, category={self.category})")


# Funções utilitárias

def create_negative_analysis(reason: str, confidence: float = 0.9) -> BugAnalysis:
    """
    Cria uma análise negativa (não é bug) com razão específica.
    
    Args:
        reason (str): Motivo pelo qual não é considerado bug
        confidence (float): Confiança na decisão
        
    Returns:
        BugAnalysis: Análise indicando que não é bug
    """
    return BugAnalysis(
        is_bug=False,
        confidence=confidence,
        description=f"Não é um bug: {reason}",
        analysis_metadata={"negative_reason": reason}
    )


def create_quick_bug_analysis(title: str, 
                             severity: BugSeverity,
                             category: BugCategory = BugCategory.UNKNOWN,
                             confidence: float = 0.8) -> BugAnalysis:
    """
    Cria uma análise rápida de bug com informações básicas.
    
    Args:
        title (str): Título do bug
        severity (BugSeverity): Severidade do bug
        category (BugCategory): Categoria do bug
        confidence (float): Confiança na análise
        
    Returns:
        BugAnalysis: Análise básica do bug
    """
    return BugAnalysis(
        is_bug=True,
        confidence=confidence,
        severity=severity,
        category=category,
        title=title,
        suggested_priority=_severity_to_priority(severity)
    )


def _severity_to_priority(severity: BugSeverity) -> str:
    """
    Converte severidade em prioridade sugerida.
    
    Args:
        severity (BugSeverity): Severidade do bug
        
    Returns:
        str: Prioridade sugerida (P0, P1, P2, P3)
    """
    mapping = {
        BugSeverity.CRITICAL: "P0",
        BugSeverity.HIGH: "P1", 
        BugSeverity.MEDIUM: "P2",
        BugSeverity.LOW: "P3"
    }
    return mapping.get(severity, "P2")