"""
IssueCreatorAgent - Agente Criador de Issues no GitHub

Localização: src/agents/issue_creator_agent.py

Responsabilidades:
- Criar issues reais no repositório GitHub
- Configurar metadados (labels, assignees, milestone)
- Tratar erros de API do GitHub
- Registrar resultado da criação
- Fornecer URL da issue criada

Este agente atua como um "publicador", responsável por
materializar as issues refinadas no GitHub usando a API oficial.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.issue_model import IssueModel, IssuePriority
from ..models.creation_model import IssueCreationResult, CreationStatus, GitHubIssueData
from ..tools.github_tool import GitHubTool, GitHubAPIError
from ..config.settings import get_settings


class IssueCreatorAgent:
    """
    Agente responsável por criar issues no GitHub.
    
    Este agente não depende de IA, focando apenas na integração
    com a API do GitHub para materializar as issues refinadas.
    """
    
    def __init__(self, github_tool: GitHubTool):
        """
        Inicializa o agente criador de issues.
        
        Args:
            github_tool: Instância da ferramenta do GitHub
        """
        self.github_tool = github_tool
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Configurações do GitHub
        self.github_config = {
            'default_repository': self.settings.get('github_repository'),
            'default_assignees': self.settings.get('github_default_assignees', []),
            'label_mapping': self._load_label_mapping(),
            'max_retries': 3,
            'retry_delay': 2.0
        }
    
    def create_issue(self, issue_draft: IssueModel) -> IssueCreationResult:
        """
        Cria uma issue no GitHub baseada no rascunho refinado.
        
        Args:
            issue_draft: Rascunho finalizado da issue
            
        Returns:
            Resultado da criação com detalhes da issue criada
        """
        try:
            self.logger.info(f"Criando issue no GitHub: {issue_draft.title[:50]}...")
            
            # Preparação dos dados para o GitHub
            github_issue_data = self._prepare_github_issue_data(issue_draft)
            
            # Validação dos dados antes do envio
            validation_result = self._validate_issue_data(github_issue_data)
            if not validation_result['is_valid']:
                return self._create_validation_error_result(issue_draft, validation_result)
            
            # Criação da issue no GitHub
            github_issue = self._create_github_issue(github_issue_data)
            
            # Configuração de metadados adicionais
            self._configure_issue_metadata(github_issue, issue_draft)
            
            # Criação do resultado de sucesso
            creation_result = self._create_success_result(issue_draft, github_issue)
            
            self.logger.info(f"Issue criada com sucesso: {github_issue.url}")
            
            return creation_result
            
        except GitHubAPIError as e:
            self.logger.error(f"Erro da API do GitHub: {str(e)}")
            return self._create_github_error_result(issue_draft, e)
        
        except Exception as e:
            self.logger.error(f"Erro inesperado durante criação da issue: {str(e)}")
            return self._create_generic_error_result(issue_draft, e)
    
    def _load_label_mapping(self) -> Dict[str, str]:
        """
        Carrega mapeamento de labels internas para labels do GitHub.
        """
        return {
            'BUG': 'bug',
            'CRITICAL': 'critical',
            'HIGH_PRIORITY': 'high-priority',
            'MEDIUM_PRIORITY': 'medium-priority', 
            'LOW_PRIORITY': 'low-priority',
            'AUTOMATED': 'automated',
            'NEEDS_REVIEW': 'needs-review',
            'DATABASE': 'database',
            'NETWORK': 'network',
            'SECURITY': 'security',
            'PERFORMANCE': 'performance',
            'UI': 'ui',
            'API': 'api',
            'BACKEND': 'backend',
            'FRONTEND': 'frontend'
        }
    
    def _prepare_github_issue_data(self, issue_draft: IssueModel) -> Dict[str, Any]:
        """
        Prepara dados da issue no formato esperado pela API do GitHub.
        """
        # Converte labels para formato do GitHub
        github_labels = self._convert_labels_to_github(issue_draft.labels)
        
        # Prepara corpo da issue com seções organizadas
        body = self._format_issue_body(issue_draft)
        
        # Monta dados da issue
        issue_data = {
            'title': issue_draft.title,
            'body': body,
            'labels': github_labels,
            'assignees': issue_draft.assignees or self.github_config['default_assignees']
        }
        
        # Adiciona milestone se especificado
        if issue_draft.milestone:
            issue_data['milestone'] = issue_draft.milestone
        
        return issue_data
    
    def _convert_labels_to_github(self, labels: List) -> List[str]:
        """
        Converte labels internas para labels do GitHub.
        """
        github_labels = []
        label_mapping = self.github_config['label_mapping']
        
        for label in labels:
            if isinstance(label):
                # Converte enum para string
                label_str = label.value
            else:
                # Já é string
                label_str = str(label)
            
            # Mapeia para label do GitHub
            github_label = label_mapping.get(label_str.upper(), label_str.lower())
            if github_label not in github_labels:
                github_labels.append(github_label)
        
        return github_labels
    
    def _format_issue_body(self, issue_draft: IssueModel) -> str:
        """
        Formata o corpo da issue com seções organizadas.
        """
        body_sections = []
        
        # Descrição principal
        body_sections.append(issue_draft.description)
        
        # Seção de passos para reprodução
        if issue_draft.reproduction_steps:
            body_sections.append("\n## Steps to Reproduce")
            for step in issue_draft.reproduction_steps:
                body_sections.append(step)
        
        # Seção de informações do ambiente
        if issue_draft.environment_info:
            body_sections.append("\n## Environment Information")
            for key, value in issue_draft.environment_info.items():
                body_sections.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Contexto adicional
        if issue_draft.additional_context:
            relevant_context = {k: v for k, v in issue_draft.additional_context.items() 
                               if not k.startswith('_') and v}  # Filtra campos internos
            
            if relevant_context:
                body_sections.append("\n## Additional Context")
                for key, value in relevant_context.items():
                    body_sections.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Metadados de criação automática
        body_sections.append("\n---")
        body_sections.append(f"*This issue was automatically created by BugFinder on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(body_sections)
    
    def _validate_issue_data(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida dados da issue antes de enviar para o GitHub.
        """
        errors = []
        warnings = []
        
        # Validações obrigatórias
        if not issue_data.get('title'):
            errors.append("Título é obrigatório")
        elif len(issue_data['title']) > 256:
            errors.append("Título muito longo (máximo 256 caracteres)")
        
        if not issue_data.get('body'):
            errors.append("Corpo da issue é obrigatório")
        elif len(issue_data['body']) > 65536:
            errors.append("Corpo da issue muito longo (máximo 65536 caracteres)")
        
        # Validações de qualidade
        if len(issue_data.get('title', '')) < 10:
            warnings.append("Título pode ser muito curto")
        
        if len(issue_data.get('body', '')) < 50:
            warnings.append("Descrição pode ser muito curta")
        
        if not issue_data.get('labels'):
            warnings.append("Nenhuma label especificada")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validated_data': issue_data
        }
    
    def _create_github_issue(self, issue_data: Dict[str, Any]) -> GitHubIssueData:
        """
        Cria a issue no GitHub usando a ferramenta.
        """
        repository = self.github_config['default_repository']
        
        if not repository:
            raise GitHubAPIError("Repositório não configurado")
        
        # Usa a ferramenta do GitHub para criar a issue
        return self.github_tool.create_issue(
            repository=repository,
            title=issue_data['title'],
            body=issue_data['body'],
            labels=issue_data.get('labels', []),
            assignees=issue_data.get('assignees', []),
            milestone=issue_data.get('milestone')
        )
    
    def _configure_issue_metadata(self, github_issue: GitHubIssueData, issue_draft: IssueModel):
        """
        Configura metadados adicionais da issue após criação.
        """
        try:
            # Se há prioridade alta, adiciona ao projeto (se configurado)
            if issue_draft.priority == IssuePriority.HIGH:
                project_id = self.settings.get('github_high_priority_project')
                if project_id:
                    self.github_tool.add_issue_to_project(github_issue.number, project_id)
            
            # Adiciona comentário com contexto técnico se houver
            technical_context = self._extract_technical_context(issue_draft)
            if technical_context:
                self.github_tool.add_issue_comment(
                    github_issue.number,
                    f"## Technical Context\n\n{technical_context}"
                )
        
        except Exception as e:
            self.logger.warning(f"Erro ao configurar metadados adicionais: {str(e)}")
            # Não falha a criação por causa de metadados opcionais
    
    def _extract_technical_context(self, issue_draft: IssueModel) -> str:
        """
        Extrai contexto técnico relevante para comentário adicional.
        """
        context_parts = []
        
        # Informações da fonte
        if issue_draft.source_log_id:
            context_parts.append(f"**Source Log ID**: `{issue_draft.source_log_id}`")
        
        if issue_draft.source_analysis_id:
            context_parts.append(f"**Analysis ID**: `{issue_draft.source_analysis_id}`")
        
        # Contexto adicional relevante
        additional = issue_draft.additional_context
        technical_fields = ['confidence_score', 'bug_type', 'criticality', 'analysis_timestamp']
        
        for field in technical_fields:
            if field in additional:
                field_name = field.replace('_', ' ').title()
                context_parts.append(f"**{field_name}**: {additional[field]}")
        
        return '\n'.join(context_parts) if context_parts else ""
    
    def _create_success_result(self, issue_draft: IssueModel, github_issue: GitHubIssueData) -> IssueCreationResult:
        """
        Cria resultado de sucesso.
        """
        return IssueCreationResult(
            status=CreationStatus.SUCCESS,
            github_issue=github_issue,
            issue_draft_id=issue_draft.id,
            created_at=datetime.now().isoformat(),
            message="Issue criada com sucesso no GitHub",
            details={
                'repository': self.github_config['default_repository'],
                'labels_applied': github_issue.labels,
                'assignees_set': github_issue.assignees,
                'creation_agent': 'IssueCreatorAgent'
            }
        )
    
    def _create_validation_error_result(self, issue_draft: IssueModel, validation: Dict[str, Any]) -> IssueCreationResult:
        """
        Cria resultado de erro de validação.
        """
        return IssueCreationResult(
            status=CreationStatus.VALIDATION_ERROR,
            github_issue=None,
            issue_draft_id=issue_draft.id,
            created_at=datetime.now().isoformat(),
            message="Dados da issue falharam na validação",
            error_details={
                'validation_errors': validation['errors'],
                'validation_warnings': validation['warnings']
            }
        )
    
    def _create_github_error_result(self, issue_draft: IssueModel, error: GitHubAPIError) -> IssueCreationResult:
        """
        Cria resultado de erro do GitHub.
        """
        return IssueCreationResult(
            status=CreationStatus.GITHUB_ERROR,
            github_issue=None,
            issue_draft_id=issue_draft.id,
            created_at=datetime.now().isoformat(),
            message=f"Erro da API do GitHub: {str(error)}",
            error_details={
                'github_error': str(error),
                'error_type': type(error).__name__,
                'repository': self.github_config['default_repository']
            }
        )
    
    def _create_generic_error_result(self, issue_draft: IssueModel, error: Exception) -> IssueCreationResult:
        """
        Cria resultado de erro genérico.
        """
        return IssueCreationResult(
            status=CreationStatus.UNKNOWN_ERROR,
            github_issue=None,
            issue_draft_id=issue_draft.id,
            created_at=datetime.now().isoformat(),
            message=f"Erro inesperado: {str(error)}",
            error_details={
                'error': str(error),
                'error_type': type(error).__name__
            }
        )
    
    def retry_failed_creation(self, issue_draft: IssueModel, previous_result: IssueCreationResult) -> IssueCreationResult:
        """
        Tenta recriar uma issue que falhou anteriormente.
        
        Args:
            issue_draft: Rascunho da issue
            previous_result: Resultado anterior que falhou
            
        Returns:
            Novo resultado da tentativa
        """
        self.logger.info(f"Tentando recriar issue após falha: {issue_draft.title[:50]}...")
        
        # Se falha foi de validação, não tenta novamente
        if previous_result.status == CreationStatus.VALIDATION_ERROR:
            self.logger.warning("Não tentando recriar issue com erro de validação")
            return previous_result
        
        # Para outros tipos de erro, tenta novamente
        return self.create_issue(issue_draft)
    
    def get_issue_url(self, creation_result: IssueCreationResult) -> Optional[str]:
        """
        Retorna URL da issue criada.
        
        Args:
            creation_result: Resultado da criação
            
        Returns:
            URL da issue ou None se não foi criada
        """
        if creation_result.status == CreationStatus.SUCCESS and creation_result.github_issue:
            return creation_result.github_issue.url
        return None
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente.
        """
        return {
            'name': 'IssueCreatorAgent',
            'version': '1.0.0',
            'description': 'Agente responsável por criar issues no GitHub',
            'capabilities': [
                'Criação de issues via API do GitHub',
                'Configuração de labels e assignees',
                'Validação de dados antes do envio',
                'Formatação adequada do corpo da issue',
                'Tratamento de erros da API',
                'Configuração de metadados adicionais',
                'Retry de criações falhadas'
            ],
            'input_format': 'IssueModel',
            'output_format': 'IssueCreationResult',
            'requires_llm': False,
            'external_dependencies': ['GitHub API'],
            'github_config': {
                'repository': self.github_config['default_repository'],
                'label_mapping_count': len(self.github_config['label_mapping']),
                'max_retries': self.github_config['max_retries']
            }
        }


# Exemplo de uso e testes
if __name__ == "__main__":
    from ..models.issue_model import IssueModel, IssuePriority
    from ..tools.github_tool import MockGitHubTool
    
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Cria agente com ferramenta mock do GitHub
    mock_github = MockGitHubTool()
    agent = IssueCreatorAgent(mock_github)
    
    # Teste: Criação de issue válida
    test_draft = IssueModel(
        title="Fix database connection timeout in UserService",
        description="""## Bug Report

### Summary
The UserService component is experiencing database connection timeouts during peak hours.

### Error Details
**Message**: Database connection failed: timeout after 30 seconds
**Component**: UserService
**Frequency**: Multiple times during peak hours

### Impact
Users cannot log in or access their profiles during high traffic periods.
""",
        labels=["bug", "automated"],
        priority=IssuePriority.HIGH,
        assignees=['dev-team'],
        reproduction_steps=[
            "1. Access application during peak hours",
            "2. Attempt login",
            "3. Observe timeout"
        ],
        environment_info={
            'service_version': 'v2.1.4',
            'database': 'PostgreSQL 13.2',
            'detection_time': '2024-01-15T10:30:45Z'
        },
        additional_context={
            'confidence_score': 0.95,
            'bug_type': 'DATABASE_ERROR',
            'criticality': 'HIGH'
        }
    )
    
    print("Teste - Criação de Issue:")
    result = agent.create_issue(test_draft)
    print(f"Status: {result.status}")
    print(f"Mensagem: {result.message}")
    
    if result.status == CreationStatus.SUCCESS:
        print(f"Issue URL: {agent.get_issue_url(result)}")
        print(f"Issue Number: {result.github_issue.number}")
        print(f"Labels aplicadas: {result.github_issue.labels}")
    else:
        print(f"Erro: {result.error_details}")
    
    # Teste: Issue com dados inválidos
    invalid_draft = IssueModel(
        title="",  # Título vazio
        description="",  # Descrição vazia
        labels=[],
        priority=IssuePriority.LOW
    )
    
    print("\nTeste - Issue Inválida:")
    invalid_result = agent.create_issue(invalid_draft)
    print(f"Status: {invalid_result.status}")
    print(f"Mensagem: {invalid_result.message}")
    if invalid_result.error_details:
        print(f"Erros de validação: {invalid_result.error_details.get('validation_errors', [])}")
    
    # Info do agente
    print("\nInfo do Agente:")
    print(json.dumps(agent.get_agent_info(), indent=2))