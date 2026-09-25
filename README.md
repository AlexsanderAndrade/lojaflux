# LojaFlux

Sistema web de gestão para pequenos comércios, inspirado em desafios observados em uma loja real. O projeto conecta compras, vendas, estoque e indicadores diários em uma experiência simples e rastreável.

> Projeto de portfólio. Todos os nomes, valores e registros da demonstração são fictícios.

## Problema de negócio

Quando compras, vendas e estoque são controlados separadamente, o responsável pela loja perde tempo conciliando informações e pode tomar decisões com dados desatualizados. O LojaFlux centraliza esses eventos e mantém o estoque sincronizado a cada operação.

## Funcionalidades do MVP

- cadastro de produtos com preço, custo e estoque mínimo;
- registro de compras com atualização de custo e entrada de estoque;
- venda com vários itens e baixa de estoque em uma única transação;
- histórico de vendas do dia;
- trilha imutável de movimentações de estoque;
- dashboard com faturamento, lucro estimado, ticket médio e alertas;
- API JSON de saúde e resumo do dashboard;
- dados demonstrativos opcionais;
- testes automatizados das regras principais.

## Decisões técnicas

- valores monetários são armazenados em centavos, evitando erros de ponto flutuante;
- vendas guardam cópias do preço e custo do momento da operação;
- compras e vendas atualizam estoque na mesma transação;
- movimentações de estoque não são apagadas, preservando rastreabilidade;
- o MVP funciona localmente com SQLite e não depende de serviços externos.

## Tecnologias

Python 3.12, Flask, SQLAlchemy, SQLite, Jinja2, HTML, CSS, JavaScript e Pytest.

## Estado

Em desenvolvimento ativo. A primeira entrega inclui fundação, banco de dados, regras de negócio, interface web responsiva e testes.

