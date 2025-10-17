# FavoriteProductsAPI · Desafio Back-end

API RESTful construída com **Django** e **PostgreSQL** para gerenciar produtos favoritos de usuários, integrando com a API externa [Fake Store API](https://fakestoreapi.com).

## Sumário

- [Funcionalidades Implementadas](#funcionalidades-implementadas)
- [Stack](#stack)
- [Pré-requisitos](#pré-requisitos)
- [Como rodar](#como-rodar)
- [Credenciais de Acesso](#credenciais-de-acesso)
- [Documentação da API](#documentação-da-api)
- [Autenticação e Autorização](#autenticação-e-autorização)
- [Modelagem](#modelagem)
- [Testes Unitários](#testes-unitários)

## Funcionalidades Implementadas

### Gestão de Clientes
- Criar, visualizar, editar e remover clientes
- Validação de e-mail único
- Campos obrigatórios: nome e e-mail
- Sistema de autenticação por token

### Produtos Favoritos
- Adicionar produtos à lista de favoritos
- Validação via API externa (Fake Store API)
- Prevenção de duplicatas na lista
- Exibição de: ID, título, imagem, preço e review
- Listagem paginada de favoritos
- Remoção de produtos favoritos

### Extras
- Sincronização automática de produtos (cronjob a cada hora)
- Documentação Swagger/OpenAPI
- Testes unitários abrangentes
- Containerização com Docker

## Stack

- **Linguagem:** Python 3.13
- **Framework:** Django 5.1 + Django Ninja
- **Banco de Dados:** PostgreSQL 16
- **Containerização:** Docker + Docker Compose
- **Documentação:** Swagger
- **Gerenciamento de Dependências:** Poetry

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Como rodar

- Clone o repositório
- Crie um arquivo .env na root do projeto. Você pode copiar as configurações disponíveis no arquivo .env.sample.
- Inicie os containers:

```
docker-compose -f docker-compose.yml up -d
```

- Acesse a aplicação:

```
API: http://localhost:8000/api
Documentação Swagger: http://localhost:8000/api/docs
Admin Django: http://localhost:8000/admin
```

## Credenciais de Acesso

- Um usuário administrador será criado automaticamente ao iniciar o projeto. As informações de login são:

```
email: admin@aiqfome.com
senha: admin
```

- Uma Token de autenticação também será gerada automaticamente. Você pode pegar ela através do painel de administrador, na seção de "AuthToken", ou fazendo uma requisição de login à API.
- O endpoint de login é: `http://localhost:8000/api/auth/login`

## Documentação da API

A documentação Swagger da API está disponível em `http://localhost:8000/api/docs`.

### Principais Endpoints

#### Autenticação (`/api/auth`)
- `POST /auth/login` - Fazer login e obter token
- `GET /auth/user` - Obter dados do usuário autenticado
- `GET /auth/token` - Obter token do usuário

#### Clientes - Uso Comum (`/api/common`)
- `POST /favorites/{product_id}` - Adicionar produto aos favoritos
- `POST /favorites/{product_id}/delete` - Remover produto dos favoritos
- `GET /favorites` - Listar produtos favoritos (paginado)

#### Gestão - Admin (`/api/management`)
- `GET /user/list` - Listar todos os usuários (paginado)
- `POST /user` - Criar novo usuário
- `GET /user/{id}` - Obter detalhes de um usuário
- `PUT /user/{id}` - Atualizar usuário
- `DELETE /user/{id}` - Deletar usuário

## Autenticação e Autorização

A autenticação é feita através de tokens de autorização. Quando um usuário é criado no sistema, uma token é gerada e associada automaticamente à ele.
Essa token deve ser enviada nos requests à API, pelo header `X-API-Key`.

A autorização é atribuida durante a criação do usuário. Usuários criados pelo administrador têm permissão de cliente, e podem acessar apenas os endpoints disponíveis nas seções `auth` e `common`.
O administrador também tem acesso aos endpoints em `management`.

Quando os requests são feitos, o sistema encontra o usuário associado à Token enviada no request e verifica a permissão.

## Modelagem

A modelagem do backend foi feita de forma simples e escalável:

- Modelo de Usuário, que armazena permissões e informações (nome, email, senha). O email de cada usuário deve ser único;
- Modelo de AuthToken, que associa tokens de autorização a usuários;
- Modelo de Produtos, que armazena as informações de produtos recebidas da API localmente;
- Modelo de ProdutosFavoritos, que associa produtos a usuários. Não pode haver uma mesma instância de ProdutosFavoritos com ID de usuário e ID de produtos iguais.

Para evitar chamadas desnecessárias e não sobrecarregar a API de produtos, toda vez que um produto é adicionado, o sistema checa se ele existe localmente. Chamadas à API são feitas somente quando um produto não é encontrado no banco de dados.

Para garantir a consistência dos dados dos produtos, um cronjob é executado a cada hora. 

Esse cronjob faz uma requisição para `https://fakestoreapi.com/products`, verifica os IDs dos produtos locais e compara os dados com o resultado da requisição.
Caso haja alguma divergência de dados em um certo produto, o produto é atualizado localmente com os dados recebidos da API.

## Testes Unitários

O projeto tem testes unitários para todos os endpoints.

É possível executar os testes com o comando: `docker-compose exec web python manage.py test`