# API de Pagamentos - SOAT Tech Challenge

Este repositório contém o **microsserviço de pagamentos** desenvolvido como parte da pós-graduação em **Arquitetura de Software** da **FIAP**. Este serviço é responsável por gerenciar todo o fluxo de pagamentos integrado ao **Mercado Pago**, desde a criação de QR codes dinâmicos até o processamento de notificações de pagamento.

## 📌 Menu

- [Integrantes](#integrantes)
- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
  - [Clean Architecture](#clean-architecture)
  - [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
  - [Comunicação Assíncrona](#comunicação-assíncrona)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração e Execução](#configuração-e-execução)
  - [Pré-requisitos](#pré-requisitos)
  - [Variáveis de Ambiente](#variáveis-de-ambiente)
  - [Build das Imagens](#build-das-imagens)
  - [Execução Local com Docker Compose](#execução-local-com-docker-compose)
- [Testes](#testes)
- [CI/CD](#cicd)
- [Implantação na AWS](#implantação-na-aws)
- [Endpoints da API](#endpoints-da-api)
- [Integração com Mercado Pago](#integração-com-mercado-pago)
- [Licença](#licença)

## Integrantes

| Nome                                       | RM       | Discord                   |
| ------------------------------------------ | -------- | ------------------------- |
| Carlos Eduardo Bastos Laet                 | RM361151 | CarlosLaet                |
| Karen Lais Martins Pontes de Fávere Orrico | RM361158 | Karen Pontes              |
| Lucas Martins Barroso                      | RM362732 | Lucas Barroso - RM362732  |
| Raphael Oliver                             | RM362129 | Raphael Oliver - RM362129 |

## Sobre o Projeto

Na **Fase 4** da pós-graduação, o projeto passou por uma transformação arquitetural significativa: a API monolítica original foi decomposta em uma **arquitetura de microsserviços**. Esta API é o microsserviço responsável exclusivamente pela gestão de pagamentos.

O sistema completo é composto por:
- **[Lambda de Autenticação](https://github.com/SOAT-Tech-Challenge-2025/lambda-identification-auth)**: Autenticação e identificação de usuários
- **[Carrinho de Compras](https://github.com/SOAT-Tech-Challenge-2025/ms-shopping-cart)**: Gerenciamento de pedidos e produtos
- **[API de Pagamentos](https://github.com/SOAT-Tech-Challenge-2025/payment-api)**: Este repositório - gerenciamento de pagamentos
- **[API de Preparação](https://github.com/SOAT-Tech-Challenge-2025/preparation-api)**: Gerenciamento da fila de preparação de pedidos
- **[Infraestrutura](https://github.com/SOAT-Tech-Challenge-2025/infrastructure)**: Terraform para VPC, EKS e API Gateway
- **[Database](https://github.com/SOAT-Tech-Challenge-2025/database)**: Gestão de bancos de dados do projeto

### Motivação da Separação

O módulo de pagamentos foi modelado desde o início do projeto como um **Bounded Context** independente, seguindo os princípios de Domain-Driven Design. No monolito original, cada contexto já era implementado como um módulo bem isolado, sem relacionamentos entre tabelas de diferentes contextos no banco de dados.

A decomposição em microsserviços na Fase 4 foi uma evolução natural dessa arquitetura, proporcionando:
- **Bounded Contexts bem definidos**: Cada microsserviço representa um contexto delimitado do domínio
- **Autonomia de dados**: Cada contexto possui seu próprio banco de dados, reforçando o isolamento
- **Escalabilidade independente**: Possibilidade de escalar cada serviço conforme sua demanda específica
- **Resiliência**: Falhas em um contexto não afetam diretamente outros contextos
- **Evolução independente**: Times podem evoluir cada bounded context de forma autônoma

## Arquitetura

### Clean Architecture

O projeto segue os princípios da **Clean Architecture**, organizando o código em camadas bem definidas:

```
payment_api/
├── domain/                        # Regras de negócio puras
│   ├── entities/                  # Entidades de domínio (Payment, Product)
│   ├── events/                    # Eventos de domínio (PaymentClosedEvent)
│   ├── value_objects/             # Objetos de valor (PaymentStatus)
│   └── ports/                     # Interfaces de saída (Repository, Gateway, Publisher)
│
├── application/                   # Casos de uso e lógica de aplicação
│   ├── commands/                  # Comandos de entrada
│   └── use_cases/                 # Implementação dos casos de uso
│       └── ports/                 # Interfaces para serviços externos
│
├── adapters/                      # Adaptadores de entrada e saída
│   ├── inbound/                   # Adaptadores de entrada
│   │   ├── rest/                  # API REST (FastAPI)
│   │   └── listeners/             # Consumer SQS (OrderCreatedListener)
│   └── out/                       # Adaptadores de saída
│       ├── mp_payment_gateway.py
│       ├── sa_payment_repository.py
│       └── boto_payment_closed_publisher.py
│
├── infrastructure/                # Configurações e detalhes técnicos
│   ├── alembic/                   # Migrations de banco de dados
│   ├── orm/                       # Modelos SQLAlchemy
│   ├── mercado_pago/              # Cliente HTTP Mercado Pago
│   ├── config.py                  # Configurações da aplicação
│   └── factory.py                 # Injeção de dependências
│
└── entrypoints/                   # Pontos de entrada da aplicação
    ├── api.py                     # FastAPI application
    └── order_created_listener.py  # Consumer de eventos
```

### Domain-Driven Design (DDD)

O domínio de pagamentos é modelado com:

**Entidades:**
- `Payment`: Representa um pagamento com ciclo de vida próprio
- `Product`: Produtos associados ao pedido

**Value Objects:**
- `PaymentStatus`: Estado do pagamento (OPENED, APPROVED, REJECTED)

**Eventos de Domínio:**
- `PaymentClosedEvent`: Disparado quando um pagamento é finalizado

**Portas (Interfaces):**
- `PaymentRepository`: Persistência de pagamentos
- `PaymentGateway`: Integração com gateway de pagamento
- `PaymentClosedPublisher`: Publicação de eventos de pagamento

### Comunicação Assíncrona

O microsserviço se comunica de forma assíncrona com outros serviços através de **AWS SNS/SQS**:

**Consumo de Eventos (SQS):**
- **OrderCreatedEvent**: Recebe notificações de pedidos criados para gerar pagamentos

**Publicação de Eventos (SNS):**
- **PaymentClosedEvent**: Notifica outros serviços quando um pagamento é finalizado (aprovado/rejeitado)

```
┌─────────────────┐      OrderCreated       ┌──────────────────┐
│ Shopping Cart   │─────────(SQS)─────────>│   Payment API    │
└─────────────────┘                         └──────────────────┘
                                                     │
                                            PaymentClosed (SNS)
                                                     │
                                                     v
                                            ┌──────────────────┐
                                            │  Preparation API │
                                            └──────────────────┘
```

## Funcionalidades

### 1. Criação de Pagamento
- Recebe evento de pedido criado via SQS
- Cria registro de pagamento no banco de dados
- Gera QR code dinâmico no Mercado Pago
- Retorna informações do pagamento com QR code

### 2. Consulta de Pagamento
- `GET /v1/payment/{payment_id}`: Busca informações de um pagamento
- Retorna status, valor total, data de expiração e informações do QR code

### 3. Renderização de QR Code
- `GET /v1/payment/{payment_id}/qr`: Gera imagem PNG do QR code
- Facilita exibição em interfaces de usuário

### 4. Webhook Mercado Pago
- `POST /v1/payment/notifications/mercado-pago`: Recebe notificações de pagamento
- Valida autenticidade através de webhook key
- Atualiza status do pagamento
- Publica evento `PaymentClosedEvent` via SNS

## Tecnologias

- **Python 3.14**: Linguagem de programação
- **Poetry**: Gerenciador de dependências e empacotamento
- **FastAPI**: Framework web assíncrono para REST API
- **Pydantic**: Validação de dados e serialização
- **SQLAlchemy + Asyncpg**: ORM assíncrono com PostgreSQL
- **Alembic**: Migrations de banco de dados
- **HTTPX**: Cliente HTTP assíncrono para Mercado Pago
- **QRCode + Pillow**: Geração de imagens QR code
- **AIOBoto3**: Cliente assíncrono AWS (SNS/SQS)
- **Pytest**: Framework de testes
- **Docker**: Containerização
- **Kubernetes**: Orquestração de containers
- **Terraform**: Infrastructure as Code
- **GitHub Actions**: CI/CD

## Estrutura do Projeto

```
payment-api/
├── payment_api/                 # Código fonte principal
│   ├── adapters/                # Camada de adaptadores
│   ├── application/             # Casos de uso
│   ├── domain/                  # Domínio do negócio
│   ├── entrypoints/             # Pontos de entrada
│   └── infrastructure/          # Configurações e infra
│
├── tests/                       # Testes unitários e integração
│   ├── unit/                    # Testes unitários
│   └── integration/             # Testes de integração
│
├── terraform/                   # Infrastructure as Code
│   ├── k8s_*.tf                 # Recursos Kubernetes
│   ├── data.tf                  # Data sources
│   ├── locals.tf                # Variáveis locais
│   ├── providers.tf             # Providers Terraform
│   └── vars.tf                  # Variáveis de entrada
│
├── docker-entrypoint/           # Scripts de inicialização
├── settings/                    # Arquivos de configuração
├── .github/workflows/           # Pipelines CI/CD
│   ├── ci_cd.yml                # Pipeline principal
│   └── destroy.yml              # Destruição de infraestrutura
│
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # Desenvolvimento local
├── docker-compose.test.yml      # Ambiente de testes
├── pyproject.toml               # Dependências Poetry
├── alembic.ini                  # Configuração Alembic
└── pytest.ini                   # Configuração Pytest
```

## Configuração e Execução

### Pré-requisitos

- Docker e Docker Compose
- Python 3.14+ (para desenvolvimento local sem Docker)
- Poetry (gerenciador de dependências Python)
- Conta no Mercado Pago com credenciais de API
- Conta AWS com acesso a SQS e SNS (para ambiente completo)

### Variáveis de Ambiente

O projeto utiliza múltiplos arquivos de configuração na pasta `settings/`. Crie os arquivos baseados nos exemplos (`.env.example`):

**settings/app.env**
```env
TITLE="SOAT Tech Challenge Payment API"
VERSION="1.0.0"
ENVIRONMENT="development"
ROOT_PATH="/soat-fast-food"
```

**settings/database.env**
```env
DSN="postgresql+asyncpg://postgres:12345@db:5432/postgres"
ECHO=False
```

**settings/mercado_pago.env**
```env
ACCESS_TOKEN="seu_access_token"
USER_ID="seu_user_id"
POS="seu_pos_id"
CALLBACK_URL="https://seu-dominio.com/soat-fast-food/v1/payment/notifications/mercado-pago"
WEBHOOK_KEY="sua_chave_webhook"
```

**settings/aws.env**
```env
REGION_NAME="us-east-1"
ACCOUNT_ID="sua_conta_aws"
ACCESS_KEY_ID="sua_access_key"
SECRET_ACCESS_KEY="sua_secret_key"
```

**settings/order_created_listener.env**
```env
QUEUE_NAME="order-created-queue"
WAIT_TIME_SECONDS=20
VISIBILITY_TIMEOUT_SECONDS=30
MAX_NUMBER_OF_MESSAGES_PER_BATCH=10
```

**settings/payment_closed_publisher.env**
```env
TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:payment-closed"
GROUP_ID="payment-closed-group"
```

### Build das Imagens

#### Desenvolvimento / Teste
```sh
docker build --target development -t payment-api:dev .
```

#### Produção
```sh
docker build --target production -t payment-api:latest .
```

### Execução Local com Docker Compose

1. **Configure as variáveis de ambiente**:
   ```sh
   cp docker-compose-env/app.env.example docker-compose-env/app.env
   cp docker-compose-env/database.env.example docker-compose-env/database.env
   ```

2. **Inicie os serviços**:
   ```sh
   docker compose up -d
   ```

3. **Execute as migrations**:
   ```sh
   docker compose exec api alembic upgrade head
   ```

4. **Acesse a API**:
   - API: http://localhost:8000
   - Documentação Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **Pare os serviços**:
   ```sh
   docker compose down
   ```

## Testes

### Executar todos os testes
```sh
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml exec api pytest
```

### Executar com cobertura
```sh
docker compose -f docker-compose.test.yml exec api pytest --cov=payment_api --cov-report=html
```

### Estrutura de Testes

- **Testes Unitários** (`tests/unit/`): Testam componentes isoladamente
- **Testes de Integração** (`tests/integration/`): Testam integrações com banco de dados e APIs externas

## CI/CD

O projeto possui pipeline completa no **GitHub Actions** com as seguintes etapas:

### Pipeline Principal (ci_cd.yml)

1. **Test**: Execução de testes unitários e de integração
2. **SonarQube**: Análise de qualidade de código e cobertura
3. **Build and Push**: Build da imagem Docker e push para ECR público
4. **Deploy**: Implantação no Kubernetes via Terraform

**Trigger**: Push em qualquer branch ou manualmente

### Pipeline de Destruição (destroy.yml)

Permite destruir a infraestrutura de forma controlada.

**Trigger**: Manual (workflow_dispatch)

## Implantação na AWS

A infraestrutura é provisionada utilizando **Terraform** e implantada em **Amazon EKS**.

### Recursos Kubernetes

- **Namespace**: `tech-challenge-payment-api`
- **Deployment**: `payment-api-deployment` (API REST)
- **Deployment**: `order-created-listener-deployment` (Consumer SQS)
- **Service**: `payment-api-service` (ClusterIP)
- **Ingress**: Roteamento via NGINX Ingress Controller
- **HPA**: Auto-scaling baseado em CPU e memória (1-3 replicas)
- **ConfigMap**: Configurações não sensíveis
- **Secret**: Credenciais e tokens

### Implantação Manual

1. **Configure backend do Terraform**:
   ```sh
   cd terraform
   cp backend.hcl.example backend.hcl
   # Edite backend.hcl com suas configurações
   ```

2. **Inicialize o Terraform**:
   ```sh
   terraform init -backend-config=backend.hcl
   ```

3. **Execute o plan**:
   ```sh
   terraform plan -var-file=terraform.tfvars
   ```

4. **Aplique as mudanças**:
   ```sh
   terraform apply -var-file=terraform.tfvars
   ```

## Endpoints da API

### Consultar Pagamento
```http
GET /soat-fast-food/v1/payment/{payment_id}
```

**Resposta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "external_id": "123456789",
  "payment_status": "OPENED",
  "total_order_value": 50.00,
  "qr_code": "00020126580014br.gov.bcb.pix...",
  "expiration": "2025-12-04T15:30:00",
  "created_at": "2025-12-04T15:15:00",
  "timestamp": "2025-12-04T15:15:00"
}
```

### Renderizar QR Code
```http
GET /soat-fast-food/v1/payment/{payment_id}/qr
```

**Resposta**: Imagem PNG do QR code

### Webhook Mercado Pago
```http
POST /soat-fast-food/v1/payment/notifications/mercado-pago?x-mp-webhook-key={key}
```

**Body:**
```json
{
  "action": "payment.created",
  "type": "payment",
  "data": {
    "id": "123456789"
  }
}
```

## Integração com Mercado Pago

O serviço utiliza a API de **QR Code Dinâmico** do Mercado Pago para processar pagamentos presenciais.

### Fluxo de Pagamento

1. **Criação do Pedido**: Carrinho de compras cria pedido e publica evento
2. **Criação do Pagamento**: Payment API recebe evento e cria QR code no Mercado Pago
3. **Exibição do QR Code**: Cliente escaneia QR code no app Mercado Pago
4. **Pagamento**: Cliente confirma pagamento no app
5. **Notificação**: Mercado Pago envia webhook para API de pagamentos
6. **Finalização**: Payment API atualiza status e publica evento de pagamento fechado

### Pré-requisitos para Testes

Para realizar os testes da integração com Mercado Pago, há duas opções:

#### Opção 1: Utilizar nossas credenciais de teste (Recomendado)

Utilize as **credenciais de teste e usuário de teste** que enviamos na entrega do projeto. Essas credenciais já estão configuradas e prontas para uso:

- Configure as variáveis de ambiente do Mercado Pago (`settings/mercado_pago.env`) com os valores fornecidos na entrega
- Utilize o **usuário de teste (comprador)** fornecido para realizar as compras no app Mercado Pago
- Teste o fluxo completo de pagamento sem necessidade de configuração adicional

#### Opção 2: Configurar sua própria integração

Caso prefira realizar sua própria integração com o Mercado Pago, siga os passos abaixo:

1. Crie uma conta **de produção** no Mercado Pago
2. Acesse o [Portal do Desenvolvedor](https://www.mercadopago.com.br/developers) e **crie uma aplicação**
3. Gere **usuários de teste** vinculados à aplicação:
   - Um usuário **vendedor**
   - Um usuário **comprador**
4. Com a conta de vendedor, crie uma aplicação no portal do desenvolvedor
5. Nas **credenciais de produção** da aplicação, obtenha:
   - `MERCADO_PAGO_ACCESS_TOKEN`: Access Token
   - `MERCADO_PAGO_USER_ID`: User ID
6. Crie uma **store** via API do Mercado Pago:
   ```
   POST https://api.mercadopago.com/users/{USER_ID}/stores
   ```
7. Crie um **POS** (ponto de venda) vinculado à store:
   ```
   POST https://api.mercadopago.com/pos
   ```
8. O valor do campo `external_store_id` do POS deve ser usado na variável `MERCADO_PAGO_POS`
9. Gere um token aleatório e seguro para configurar como `MERCADO_PAGO_WEBHOOK_KEY`

### Como Testar o Fluxo de Pagamento

Para que o Mercado Pago consiga notificar a finalização do pagamento, a API precisa estar **acessível na web**.

A URL configurada em `MERCADO_PAGO_CALLBACK_URL` deve seguir o formato:

```
https://{ENDERECO_DA_API}/soat-fast-food/v1/payment/notifications/mercado-pago
```

### Variáveis de Ambiente do Mercado Pago

Configure as seguintes variáveis no arquivo `settings/mercado_pago.env`:

- `ACCESS_TOKEN`: Token de autenticação da API do Mercado Pago
- `USER_ID`: ID do usuário vinculado à aplicação
- `POS`: Valor de `external_store_id` do POS criado via API
- `CALLBACK_URL`: URL que receberá notificações de pagamento (webhook)
- `WEBHOOK_KEY`: Token usado como parâmetro de query para validar as notificações

### Segurança

- Webhook protegido por key de autenticação (query parameter)
- Validação de assinatura do webhook
- HTTPS obrigatório em produção

## Licença

Este projeto está licenciado sob a **Apache License 2.0**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

Desenvolvido para fins educacionais como parte da pós-graduação em Arquitetura de Software da FIAP.

---

**Documentação complementar**: Para entender o sistema completo, consulte os repositórios dos demais microsserviços listados na seção [Sobre o Projeto](#sobre-o-projeto).
