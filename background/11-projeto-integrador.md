# Módulo 11 — Projeto Integrador

> *"Tudo que você aprendeu até aqui agora se converge em algo que funciona de verdade."*

## Objetivos

O projeto integrador é a **avaliação final** da disciplina. Vale **25 % da nota**.

O objetivo é integrar **todo o conhecimento adquirido** em um sistema coerente, similar ao que você encontrará em sua vida profissional.

---

## Cenário do Projeto

Sua equipe foi contratada como **engenharia de automação** para uma pequena estação de bombeamento. A planta inclui:

- **2 motores trifásicos** acionados por inversores de frequência (simulados pelo ModbusDeviceSIM **MK-VFD7**)
- **1 medidor de energia** monitorando o quadro geral (ModbusDeviceSIM **MK-EM3P**)
- **1 SCADA local** para operação
- **1 dashboard remoto** para monitoramento da gerência

Sua tarefa: **projetar, implementar e validar** esse sistema usando o que aprendeu.

---

## Requisitos Funcionais

### RF-01 — Aquisição de dados do medidor

O sistema deve **ler continuamente** do medidor MK-EM3P:

- Tensão L1, L2, L3 (V)
- Corrente L1, L2, L3 (A)
- Potência ativa total (kW)
- Fator de potência total
- Frequência (Hz)
- Energia ativa acumulada (kWh)

**Taxa de atualização:** mínimo 1 leitura/segundo.

### RF-02 — Controle dos inversores

Para cada motor (Inversor 1, Inversor 2), o operador deve poder:

- **Ligar/desligar** o motor (Control Word)
- **Selecionar sentido** de rotação (forward/reverse)
- **Ajustar referência de frequência** (Hz, valor decimal)
- **Visualizar** frequência atual, velocidade (RPM), corrente (A) e status

### RF-03 — SCADA local

Implementar em **Node-RED** ou Python+Tkinter um **painel de operação**:

- Dashboard com **gráficos** em tempo real
- **Botões** de controle por motor
- **Indicadores** de alarme

### RF-04 — Alarmes

O sistema deve detectar e indicar visualmente:

- **Sobre-corrente** em qualquer fase do medidor (> 25 A)
- **Falha** em qualquer inversor (fault code ≠ 0)
- **Sub-tensão** (qualquer fase < 200 V)

### RF-05 — Histórico

Implementar **logging em arquivo CSV** ou banco SQLite:

- Todas as medições a cada 10 segundos
- Eventos de start/stop dos inversores
- Eventos de alarme com timestamp

### RF-06 — Acesso remoto (bônus)

(Opcional, +5 % na nota)

Expor o dashboard via **MQTT** ou **HTTP** para acesso de fora da rede local.

---

## Requisitos Não-Funcionais

### RNF-01 — Confiabilidade

- O sistema **não pode travar** se a rede cair temporariamente.
- Reconexão automática em falha de comunicação.

### RNF-02 — Documentação

- **README.md** explicando arquitetura e como executar
- **Diagrama de blocos** do sistema
- **Mapa Modbus** documentado (endereços usados)

### RNF-03 — Versionamento

- Código em **Git**
- Commits frequentes com mensagens claras
- README com instruções de instalação

### RNF-04 — Apresentação

- Defesa oral de **15 minutos** + 10 min de perguntas
- Apresentação com slides e demo ao vivo

---

## Tecnologias Permitidas

- **Python** com pymodbus (preferido)
- **Node-RED** para SCADA/dashboard
- **Node.js** se a equipe preferir
- **SQLite** ou CSV para histórico
- **MQTT** (Mosquitto local) para distribuição (opcional)

**Bibliotecas proibidas (queremos que vocês entendam o que está acontecendo):**
- Frameworks SCADA prontos (Ignition, ScadaBR já configurados)
- Bibliotecas wrapper de alto nível que escondam o protocolo

---

## Arquitetura Sugerida

```
   ┌──────────────────────────────────────────────────────┐
   │                  Smartphone Android                  │
   │       ModbusDeviceSIM (MK-EM3P + MK-VFD7 × 2)        │
   │              Modbus TCP server :5020                 │
   └──────────────────────────────────────────────────────┘
                            │
                            │  Wi-Fi
                            │
   ┌──────────────────────────────────────────────────────┐
   │                       Laptop                         │
   │                                                      │
   │   ┌─────────────────────────────────────────────┐    │
   │   │ Cliente Modbus TCP (Python ou Node-RED)     │    │
   │   │  - polling contínuo                          │    │
   │   │  - decodificação FLOAT32                     │    │
   │   │  - tratamento de erros                       │    │
   │   └────────────────┬────────────────────────────┘    │
   │                    │                                 │
   │                    ▼                                 │
   │   ┌─────────────────────────────────────────────┐    │
   │   │ Backend de processamento                    │    │
   │   │  - cálculo de alarmes                        │    │
   │   │  - persistência                              │    │
   │   └────────────────┬────────────────────────────┘    │
   │                    │                                 │
   │                    ▼                                 │
   │   ┌─────────────────────────────────────────────┐    │
   │   │ Dashboard (Node-RED ou web)                 │    │
   │   │  - gauges, gráficos, controles              │    │
   │   └─────────────────────────────────────────────┘    │
   │                                                      │
   │   ┌─────────────────────────────────────────────┐    │
   │   │ Histórico (SQLite ou CSV)                   │    │
   │   └─────────────────────────────────────────────┘    │
   └──────────────────────────────────────────────────────┘
```

> **Nota:** o ModbusDeviceSIM atual roda **um único dispositivo por vez**. Para simular **dois VFDs**, sua equipe pode:
> - Rodar duas instâncias em telefones diferentes
> - Rodar uma instância Python no laptop em loopback + uma no telefone
> - Estender o ModbusDeviceSIM para suportar múltiplos dispositivos (bonus técnico — não é exigido)

---

## Entregas

### Semana 12 — Projeto aprovado

- Apresentação de **proposta** (5 min): arquitetura, divisão de tarefas, cronograma.
- Aprovação pelo professor.

### Semana 14 — Apresentação parcial

- Demo funcional dos requisitos **RF-01 e RF-02**.

### Semana 15 — Defesa final

- Demo completa do sistema com todos os requisitos.
- Defesa oral.
- Entrega do código completo via Git.
- Entrega do **relatório técnico** (mínimo 10 páginas).

---

## Critérios de Avaliação

| Critério                                         | Peso |
|--------------------------------------------------|------|
| Cumprimento dos requisitos funcionais            | 30%  |
| Qualidade técnica do código                      | 20%  |
| Tratamento de erros e robustez                   | 15%  |
| Documentação e versionamento                     | 10%  |
| Análise crítica e discussão técnica              | 10%  |
| Apresentação oral                                | 10%  |
| Funcionalidades extras (bônus)                   | +5%  |

---

## Estrutura Sugerida do Relatório Técnico

```
   1. Introdução
   2. Especificação do problema
   3. Arquitetura proposta
      3.1 Diagrama de blocos
      3.2 Tecnologias escolhidas
      3.3 Justificativas
   4. Implementação
      4.1 Cliente Modbus
      4.2 Processamento de dados
      4.3 Dashboard
      4.4 Persistência
      4.5 Alarmes
   5. Testes
      5.1 Cenários de teste
      5.2 Resultados
      5.3 Capturas de tela
   6. Discussão
      6.1 Limitações do sistema
      6.2 Melhorias propostas
      6.3 Lições aprendidas
   7. Conclusão
   8. Referências
   Apêndice A — Mapa Modbus utilizado
   Apêndice B — Listagens de código relevantes
```

---

## Dicas de Sucesso

### Comece simples

Não tente fazer tudo de uma vez. Comece com **ler um único registrador** e exibi-lo. Depois evolua.

### Use Git desde o dia 1

Faça commits frequentes. Documente decisões nas mensagens. Use branches para experimentos.

### Teste falhas

Não basta o "caminho feliz". Teste:
- O que acontece se o smartphone fica fora do Wi-Fi?
- O que acontece se o operador apertar dois botões muito rápido?
- O que acontece se você ler um endereço inválido?

### Documente conforme implementa

Escrever o relatório no final, com 3 dias para entregar, é receita para desastre. Documente cada feature **assim que termina**.

### Comunicação na equipe

A maioria dos projetos não falha tecnicamente — falham por **falta de coordenação**. Tenham um canal de comunicação claro e reuniões frequentes.

### Peça ajuda

Vocês têm acesso ao professor durante o horário de orientação. Aproveitem antes da última semana.

---

## Lista de Verificação Final (antes da entrega)

- [ ] Todos os 6 requisitos funcionais implementados
- [ ] Documentação atualizada (README, diagrama, mapa Modbus)
- [ ] Código commitado e push para o repositório
- [ ] Relatório técnico finalizado (PDF)
- [ ] Demo testada **2 vezes** antes da apresentação
- [ ] Apresentação treinada com o tempo cronometrado
- [ ] Backup do código e relatório (não confie em um único pendrive)

---

## Considerações Finais

Este projeto é, ao mesmo tempo, **a culminação** desta disciplina e **uma simulação** do que vocês farão em suas carreiras profissionais. O Modbus TCP é apenas uma ferramenta; o que importa é a sua **capacidade de raciocinar sobre sistemas industriais**: requisitos, restrições, integração, robustez, manutenibilidade.

Boas práticas que vão **muito além do Modbus**:

1. **Pense no usuário final.** O operador da estação não é engenheiro.
2. **Falhe explicitamente.** Erros silenciosos são piores que erros gritantes.
3. **Documente assumindo que outros lerão.** (Provavelmente você mesmo, daqui a 6 meses.)
4. **Versione tudo.** Inclusive arquivos de configuração.
5. **Teste em condições reais.** Wi-Fi fraco, smartphone com pouca bateria, latência variável.

---

**Boa sorte. E que vocês construam algo de que se orgulhem.**

— **Prof. Dênis Leite**
*Mekatronik — Advanced Engineering*

---

## Recursos Finais para Consulta

- Lab Guides na pasta `docs/lab-tasks/`:
  - `lab-guide-easymodbustcp.md` — para revisão do protocolo
  - `lab-guide-codesys.md` — para integração com CLP (opcional, para alunos interessados em CLP)
- Código fonte do **ModbusDeviceSIM** (`modbusdevicesim/` e `android-simulator/`)
- Documentação **pymodbus**: [https://pymodbus.readthedocs.io](https://pymodbus.readthedocs.io)
- Documentação **Node-RED**: [https://nodered.org/docs](https://nodered.org/docs)
- Documentação **Modbus Organization**: [https://modbus.org](https://modbus.org)
