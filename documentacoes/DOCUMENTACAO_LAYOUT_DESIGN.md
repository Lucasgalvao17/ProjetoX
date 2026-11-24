# ATILA V2 — Documentação de Layout e Design

## 1. Introdução

O ATILA V2 possui uma interface web desenvolvida para facilitar a navegação e a utilização das funcionalidades de gerenciamento e agendamento de salas. O layout foi pensado para organizar as informações de maneira clara, permitindo que o usuário acesse diferentes áreas do sistema sem precisar navegar por telas desnecessariamente complexas.

A interface utiliza o Streamlit como base para construção das páginas, com personalizações de layout e CSS para melhorar a organização visual e a apresentação dos componentes.

## 2. Estrutura visual do sistema

O sistema foi organizado em uma estrutura composta por áreas principais:

- **Barra lateral de navegação:** responsável por disponibilizar os menus e funcionalidades.
- **Área principal de conteúdo:** espaço destinado à apresentação das páginas, formulários, tabelas e informações.
- **Cabeçalho e identificação:** apresentação do título e informações relacionadas à página atual.
- **Componentes interativos:** botões, formulários, seletores, filtros, tabelas e mensagens de retorno.

A organização busca manter uma estrutura consistente entre as páginas, facilitando o entendimento e a utilização do sistema.

## 3. Barra lateral de navegação

A barra lateral é um dos principais elementos de organização do ATILA V2. Ela permite que o usuário navegue entre as funcionalidades disponíveis após realizar o login.

O menu lateral contém as seguintes opções:

- Dashboard
- Salas
- Nova Reserva
- Agendamentos
- Usuários
- Disciplinas
- Meu Perfil
- Sair

Além dos menus, a barra lateral apresenta informações do usuário conectado, como nome e perfil de acesso.

Essa estrutura permite que as funcionalidades estejam centralizadas em um único local, facilitando a navegação e evitando que o usuário precise retornar constantemente à página inicial.

## 4. Dashboard

O Dashboard é a tela principal apresentada após o acesso ao sistema. Seu objetivo é fornecer uma visão geral das informações relacionadas ao gerenciamento de salas e reservas.

O painel apresenta indicadores que ajudam a acompanhar a situação do sistema.

### Elementos do Dashboard

- Quantidade total de salas cadastradas.
- Quantidade total de reservas.
- Quantidade de reservas confirmadas.
- Quantidade de usuários cadastrados.
- Tabela com informações gerais das salas.
- Tabela com os agendamentos mais recentes.

A organização dos indicadores permite que o administrador ou usuário tenha uma visão rápida das principais informações antes de acessar outras funcionalidades.

## 5. Tela de Login

A tela de login é responsável pelo acesso inicial ao sistema. Nela, o usuário pode entrar em uma conta existente ou realizar a criação de uma nova conta.

### Elementos presentes

- Identificação visual do ATILA.
- Descrição do sistema: Gestão e Agendamento de Salas.
- Campo para e-mail.
- Campo para senha.
- Botão de acesso.
- Opção para criação de conta.

A tela foi desenvolvida para centralizar o acesso ao sistema, permitindo que os usuários iniciem sua utilização de maneira simples.

## 6. Tela de criação de conta

A criação de conta permite que novos usuários sejam cadastrados no sistema.

O formulário apresenta campos para:

- Nome.
- E-mail.
- Senha.
- Confirmação de senha.
- Perfil de usuário.

A interface possui validações para verificar se as senhas correspondem, se os campos necessários foram preenchidos e se o e-mail já está cadastrado.

## 7. Tela de gerenciamento de salas

A página de salas permite visualizar e cadastrar os ambientes disponíveis na instituição.

### Organização dos campos

- Nome da sala.
- Capacidade.
- Tipo de sala.
- Campus.
- Prédio.
- Andar.
- Número.
- Quantidade de computadores.
- Projetor.
- Ar-condicionado.
- Acessibilidade.
- Observações.

A tela também permite a consulta das salas cadastradas, enquanto as operações administrativas ficam disponíveis de acordo com o perfil de acesso.

## 8. Tela de Nova Reserva

A tela Nova Reserva foi desenvolvida para permitir que usuários solicitem a utilização de uma sala.

O formulário é organizado para reunir as informações necessárias ao agendamento.

### Campos e informações

- Professor ou solicitante.
- Disciplina.
- Tipo de aula.
- Quantidade de alunos.
- Data.
- Horário de início.
- Horário de término.
- Sala.
- Justificativa.

A tela também apresenta o processo de recomendação de salas, auxiliando na escolha de um ambiente que atenda à quantidade de alunos e, quando necessário, à quantidade de computadores.

## 9. Tela de Agendamentos

A página de agendamentos permite visualizar e acompanhar as solicitações realizadas no sistema.

### Recursos da interface

- Tabela de agendamentos.
- Filtro por status.
- Filtro por sala.
- Pesquisa por professor.
- Pesquisa por disciplina.
- Área administrativa para alteração do status das reservas.

Os administradores podem gerenciar o status das solicitações, como Pendente, Confirmada, Reprovada ou Cancelada.

## 10. Tela de Usuários

A tela de usuários foi desenvolvida para permitir o acompanhamento das contas cadastradas.

Os administradores podem visualizar os usuários e realizar a ativação ou desativação de contas.

Para os demais perfis, a interface restringe as operações administrativas, permitindo a visualização das informações disponíveis conforme as permissões do sistema.

## 11. Tela de Disciplinas

A página de disciplinas permite cadastrar e consultar as disciplinas utilizadas no processo de agendamento.

### Campos do formulário

- Nome da disciplina.
- Código.
- Curso.

A organização da página permite manter as disciplinas centralizadas, facilitando sua utilização durante o preenchimento de novas reservas.

## 12. Tela Meu Perfil

A tela Meu Perfil apresenta as informações básicas do usuário que está conectado ao sistema.

### Informações exibidas

- Nome.
- E-mail.
- Perfil de acesso.
- Situação da conta.

Nesta versão, os dados são apresentados para consulta, sem funcionalidades de edição.

## 13. Organização dos componentes

A interface do ATILA V2 utiliza diferentes componentes para facilitar a interação com o sistema.

| Componente | Utilização |
|---|---|
| Botões | Executar ações como cadastrar, confirmar e sair. |
| Formulários | Inserir informações para cadastro e reservas. |
| Tabelas | Apresentar dados de salas, usuários e agendamentos. |
| Filtros | Facilitar a busca de informações. |
| Seletores | Permitir escolha de salas, disciplinas e status. |
| Indicadores | Apresentar informações resumidas no Dashboard. |
| Mensagens | Informar erros, confirmações e resultados das operações. |
| Menu lateral | Organizar a navegação entre páginas. |

## 14. Organização e padrão visual

O projeto utiliza uma configuração visual centralizada, por meio do arquivo `views/layout.py`, responsável pela configuração geral da interface e pelo menu lateral.

Entre as características da estrutura visual estão:

- Layout amplo para melhor utilização do espaço disponível.
- Barra lateral expandida para facilitar o acesso às funcionalidades.
- Personalização de elementos visuais utilizando CSS.
- Organização das páginas por funcionalidades.
- Padronização da navegação.
- Utilização de ícone relacionado ao ambiente de salas.
- Identificação visual do sistema ATILA.

A centralização da configuração visual contribui para manter uma organização entre as diferentes páginas e facilita possíveis alterações futuras no design.

## 15. Experiência de utilização (UX)

A experiência de utilização do ATILA V2 foi pensada para que as principais funcionalidades estejam acessíveis de forma organizada.

A navegação por menu lateral permite que o usuário encontre rapidamente a página desejada, enquanto os formulários concentram as informações necessárias para cada operação.

A utilização de tabelas facilita a consulta de dados, e os indicadores do Dashboard auxiliam no acompanhamento das atividades.

O controle de acesso também contribui para a organização da experiência, apresentando funcionalidades conforme o perfil do usuário.

## 16. Organização das páginas

A estrutura visual foi dividida de acordo com as responsabilidades de cada funcionalidade.

| Página | Finalidade |
|---|---|
| Login | Acesso e criação de contas. |
| Dashboard | Visão geral do sistema. |
| Salas | Cadastro e consulta de ambientes. |
| Nova Reserva | Solicitação de agendamento. |
| Agendamentos | Consulta e gerenciamento de reservas. |
| Usuários | Consulta e controle de contas. |
| Disciplinas | Cadastro e consulta de disciplinas. |
| Meu Perfil | Visualização das informações do usuário. |

## 17. Considerações finais

O layout do ATILA V2 foi organizado para oferecer uma interface funcional, com navegação centralizada e páginas separadas de acordo com as atividades do sistema.

A utilização do Streamlit, aliada à personalização de layout e CSS, possibilitou a construção de uma interface que reúne as principais funcionalidades de gerenciamento de salas e agendamentos.

A estrutura visual também permite futuras melhorias, como a implementação de calendário visual, gráficos adicionais, notificações, ajustes de responsividade e novas personalizações de design.

O projeto busca unir organização, funcionalidade e facilidade de utilização, contribuindo para uma experiência mais eficiente no gerenciamento de salas de uma instituição de ensino.

---

**Projeto: ATILA V2 — Sistema de Gestão e Agendamento de Salas**

**Tecnologias:** Python, Streamlit, Pandas, CSV e CSS.

**Arquitetura:** Organização baseada em MVC.

**Finalidade:** Projeto acadêmico de desenvolvimento de sistema web.
