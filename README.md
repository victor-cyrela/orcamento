# Radar Orçamentário

Dashboard em Streamlit para comparar previsões orçamentárias de condomínios, padronizar tipos de gasto com base em uma biblioteca de regras e destacar divergências entre arquivos.

## O que o projeto faz

- Carrega 2 a 4 previsões em Excel (`.xlsx` ou `.xlsm`)
- Identifica automaticamente layouts comuns de planilhas orçamentárias
- Padroniza os itens por classificação de gasto
- Compara previsões lado a lado
- Exibe itens não classificados para revisão
- Exporta a comparação consolidada para Excel

## Estrutura esperada da biblioteca

O app já inclui uma biblioteca padrão em `data/default_library.csv`.

Se quiser substituir por uma biblioteca própria, envie um arquivo `.csv`, `.xlsx` ou `.xlsm` contendo pelo menos estas colunas:

- `pattern`
- `classification_display`

Colunas opcionais:

- `priority`
- `scope` (`description`, `section` ou `both`)

Exemplo:

| pattern | classification_display | priority | scope |
|---|---|---:|---|
| manutencao|elevador | Manutenção e Conservação | 40 | both |
| agua|esgoto|light | Concessionárias | 30 | both |

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy no Streamlit Community Cloud

1. Suba este repositório no GitHub.
2. No Streamlit Community Cloud, conecte o repositório.
3. Defina o arquivo principal como `streamlit_app.py`.
4. O deploy usará automaticamente o `requirements.txt` e `.streamlit/config.toml`.

## Observações importantes

- Quando a planilha tiver apenas uma coluna de valor, o app replica esse valor em `90 dias` e `Cota Plena` para manter a comparação funcional.
- Itens que não encontrarem correspondência na biblioteca aparecem em **Avisos e exceções**.
- A exportação gera um arquivo consolidado com resumo, detalhes e itens não classificados.
