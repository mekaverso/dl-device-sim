# Plano de Ensino — Comunicações Industriais e Protocolo Modbus

**Empresa/Instituição:** Mekatronik — Advanced Engineering
**Professor responsável:** Prof. Dênis Leite
**Disciplina:** Comunicações Industriais e Protocolo Modbus
**Carga horária:** 60 horas (45 h teoria + 15 h prática de laboratório)
**Pré-requisitos:** Eletrônica Digital I, Sistemas Digitais, Redes de Computadores (desejável)
**Público-alvo:** Estudantes de Engenharia em Automação Industrial / Engenharia Elétrica / Engenharia de Controle

---

## 1. Ementa

Fundamentos de comunicação serial assíncrona. Padrões físicos RS-232 e RS-485: características elétricas, topologias, limitações e aplicações industriais. Protocolo Modbus: modelo de dados, modos de transmissão (RTU, ASCII, TCP). Fundamentos de redes TCP/IP. Modbus TCP: estrutura, encapsulamento e particularidades. Ferramentas de teste, diagnóstico e simulação. Implementação prática em diferentes linguagens e ambientes (EasyModbusTCP, Python, Node-RED).

---

## 2. Objetivos da Disciplina

### 2.1 Objetivo geral

Capacitar o aluno a compreender, projetar e diagnosticar sistemas de comunicação industrial baseados em comunicação serial e Modbus, com domínio do protocolo Modbus TCP e das ferramentas modernas de teste e integração.

### 2.2 Objetivos específicos

Ao final da disciplina, o aluno deverá ser capaz de:

1. **Explicar** os princípios físicos e lógicos da comunicação serial assíncrona, incluindo enquadramento, paridade, taxa de transmissão e modos duplex.
2. **Diferenciar** os padrões RS-232 e RS-485, identificando suas características elétricas, vantagens, limitações e aplicações apropriadas.
3. **Decompor** um frame Modbus RTU em seus campos constituintes e calcular o CRC-16 para validação.
4. **Configurar** redes TCP/IP de pequeno e médio porte para integração de dispositivos industriais.
5. **Implementar** clientes e servidores Modbus TCP em Python utilizando bibliotecas modernas.
6. **Diagnosticar** problemas de comunicação utilizando ferramentas como Wireshark, EasyModbusTCP e analisadores serial.
7. **Projetar** soluções de integração industrial utilizando Node-RED como middleware.
8. **Avaliar** criticamente a escolha entre Modbus RTU e Modbus TCP em função do contexto da aplicação.

---

## 3. Estrutura Modular

| Módulo | Título                                            | Carga (h) | Tipo       |
|--------|---------------------------------------------------|-----------|------------|
| 1      | Introdução às Comunicações Industriais            | 4         | Teórica    |
| 2      | Fundamentos de Comunicação Serial Assíncrona      | 6         | Teórica    |
| 3      | Padrão RS-232 — Eletrônica e Aplicação            | 4         | Teórica    |
| 4      | Padrão RS-485 — Robustez Industrial               | 6         | Teórica + 1h Prática |
| 5      | Introdução ao Protocolo Modbus                    | 4         | Teórica    |
| 6      | Modbus RTU — Anatomia do Protocolo                | 8         | Teórica + 2h Prática |
| 7      | Modbus ASCII — Aspectos Específicos               | 2         | Teórica    |
| 8      | Fundamentos de Redes TCP/IP                       | 6         | Teórica    |
| 9      | Modbus TCP — Encapsulamento e Particularidades    | 6         | Teórica + 2h Prática |
| 10     | Visão Geral das Práticas                          | 0,5       | Orientação |
| 11-13  | Práticas com MK-EM3P (medidor): EasyModbus, Python, Node-RED | 5,5 | Prática individual |
| 14-16  | Práticas com MK-VFD7 (VFD): EasyModbus, Python, Node-RED     | 5,5 | Prática individual |
| 17     | Prática em Grupo Multi-dispositivos               | 4         | Prática em grupo |

---

## 4. Metodologia

- **Aulas expositivas dialogadas** com uso intensivo de diagramas, simuladores e exemplos reais de equipamentos industriais.
- **Análise prática** de frames capturados com analisadores lógicos e Wireshark.
- **Laboratórios guiados** com material próprio (ModbusDeviceSIM) e ferramentas de mercado.
- **Estudos de caso** baseados em equipamentos comerciais (medidores de energia, inversores de frequência, CLPs).
- **Projeto integrador** final, em equipe, simulando integração de planta industrial.

---

## 5. Avaliação

| Instrumento                                    | Peso |
|------------------------------------------------|------|
| Prova teórica I — Comunicação serial e Modbus RTU | 25%  |
| Prova teórica II — TCP/IP e Modbus TCP         | 25%  |
| Relatórios de laboratório (8 práticas)         | 25%  |
| Projeto integrador final                       | 25%  |

> **Critério de aprovação:** média ponderada ≥ 6,0 e frequência ≥ 75 %.

---

## 6. Bibliografia

### 6.1 Básica

1. **Modbus Organization.** *Modbus Application Protocol Specification V1.1b3* (2012). [modbus.org](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
2. **Modbus Organization.** *Modbus Messaging on TCP/IP Implementation Guide V1.0b* (2006).
3. **Modbus Organization.** *Modbus over Serial Line Specification V1.02* (2006).
4. **TIA/EIA-485-A** — *Electrical Characteristics of Generators and Receivers for Use in Balanced Digital Multipoint Systems*.
5. **TIA-232-F** — *Interface Between Data Terminal Equipment and Data Circuit-Terminating Equipment Employing Serial Binary Data Interchange*.

### 6.2 Complementar

6. **Tanenbaum, A. S.; Wetherall, D. J.** *Redes de Computadores*. 5ª ed. Pearson, 2011.
7. **Lugli, A. B.; Santos, M. M. D.** *Sistemas Fieldbus para Automação Industrial*. Érica, 2009.
8. **Mackay, S. et al.** *Practical Industrial Data Networks: Design, Installation and Troubleshooting*. Newnes, 2004.
9. **Documentação pymodbus:** [https://pymodbus.readthedocs.io](https://pymodbus.readthedocs.io)
10. **Node-RED Documentation:** [https://nodered.org/docs](https://nodered.org/docs)

---

## 7. Cronograma Sugerido (semestre de 15 semanas)

| Semana | Conteúdo                                                       |
|--------|----------------------------------------------------------------|
| 1      | Módulo 1: Por que comunicar? Visão histórica e contexto        |
| 2      | Módulo 2: Comunicação serial — bits, frames, UART              |
| 3      | Módulo 2: Paridade, baud rate, simplex/duplex                  |
| 4      | Módulo 3: RS-232 — eletrônica, pinagem, handshaking            |
| 5      | Módulo 4: RS-485 — sinalização diferencial e multidrop         |
| 6      | Módulo 4: Lab 01 — Comunicação serial RS-232 entre dois PCs    |
| 7      | Módulo 5: Origem do Modbus, modelo de dados                    |
| 8      | Módulo 6: Modbus RTU — frame, function codes, CRC-16           |
| 9      | Módulo 6: Lab 02 — Modbus RTU com EasyModbus e simulador       |
| 10     | **Prova teórica I** + Módulo 7: Modbus ASCII                   |
| 11     | Módulo 8: TCP/IP — endereçamento, sockets, portas              |
| 12     | Módulo 9: Modbus TCP — MBAP, encapsulamento                    |
| 13     | Práticas 1-3: MK-EM3P (EasyModbus, Python, Node-RED)           |
| 14     | Práticas 4-6: MK-VFD7 (EasyModbus, Python, Node-RED)           |
| 15     | **Prova teórica II** + Prática 7 em grupo (multi-dispositivos) |

---

## 8. Recursos e Equipamentos de Laboratório

- Computadores com Windows 10/11
- Conversores USB ↔ RS-232 (par)
- Conversores USB ↔ RS-485
- Cabos par trançado blindado (STP)
- Resistores de terminação 120 Ω
- Smartphones Android (para uso com ModbusDeviceSIM)
- Software: Python 3.10+, Node-RED, EasyModbusTCP, Wireshark, com0com (Windows)
- Aplicativo proprietário: **ModbusDeviceSIM** (Mekatronik — simulador de medidor de energia e inversor de frequência)

---

## 9. Organização dos Materiais Didáticos

Esta disciplina é acompanhada por uma série de documentos em `background/`:

| Arquivo | Conteúdo |
|---------|----------|
| `00-plano-de-ensino.md`                          | Este documento — plano-mestre |
| `01-introducao-comunicacoes-industriais.md`      | Contexto, motivação e histórico |
| `02-fundamentos-comunicacao-serial.md`           | Bits, frames, UART, paridade, baud rate |
| `03-padrao-rs232.md`                             | Especificação, pinagem, limitações |
| `04-padrao-rs485.md`                             | Diferencial, multidrop, terminação |
| `05-introducao-modbus.md`                        | História, filosofia, modelo de dados |
| `06-modbus-rtu.md`                               | Frame, CRC-16, function codes, timing |
| `07-modbus-ascii.md`                             | Variante ASCII e LRC |
| `08-fundamentos-tcp-ip.md`                       | IP, TCP, UDP, sockets, portas |
| `09-modbus-tcp.md`                               | MBAP, encapsulamento, porta 502 |
| `10-praticas-visao-geral.md`                     | Visão geral e índice das práticas |
| `11-pratica-em3p-easymodbus.md`                  | Prática 1: medidor com EasyModbusTCP |
| `12-pratica-em3p-python.md`                      | Prática 2: medidor com Python |
| `13-pratica-em3p-nodered.md`                     | Prática 3: medidor com Node-RED |
| `14-pratica-vfd7-easymodbus.md`                  | Prática 4: VFD com EasyModbusTCP |
| `15-pratica-vfd7-python.md`                      | Prática 5: VFD com Python |
| `16-pratica-vfd7-nodered.md`                     | Prática 6: VFD com Node-RED |
| `17-pratica-grupo-multi-dispositivos.md`         | Prática 7: 3 alunos, 3 smartphones, 3 laptops |

---

**Prof. Dênis Leite**
Mekatronik — Advanced Engineering
*Versão: 2026.1*
