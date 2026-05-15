# Disciplina: Comunicações Industriais e Protocolo Modbus

**Empresa/Instituição:** Mekatronik — Advanced Engineering
**Professor:** Prof. Dênis Leite
**Público-alvo:** Estudantes de Engenharia em Automação Industrial / Engenharia Elétrica / Engenharia de Controle
**Carga horária:** 60 horas (45 h teoria + 15 h prática)
**Idioma:** Português

---

## Sobre esta disciplina

Material didático completo para uma disciplina de **comunicações industriais** com foco no protocolo Modbus, construído de forma **progressiva e didática**:

> O aluno entra na disciplina **sem conhecer nada** sobre comunicações industriais e sai dela **com domínio** sobre comunicação serial, fundamentos de TCP/IP, e **expertise** em Modbus TCP, tendo praticado com ferramentas reais.

---

## Índice dos Módulos

| Módulo | Arquivo | Tema | Carga |
|--------|---------|------|-------|
| 0 | [00-plano-de-ensino.md](00-plano-de-ensino.md) | Plano de ensino e ementa | — |
| 1 | [01-introducao-comunicacoes-industriais.md](01-introducao-comunicacoes-industriais.md) | Contexto, histórico e motivação | 4 h |
| 2 | [02-fundamentos-comunicacao-serial.md](02-fundamentos-comunicacao-serial.md) | Comunicação serial assíncrona, UART, paridade | 6 h |
| 3 | [03-padrao-rs232.md](03-padrao-rs232.md) | Padrão RS-232: eletrônica e aplicação | 4 h |
| 4 | [04-padrao-rs485.md](04-padrao-rs485.md) | Padrão RS-485: robustez industrial | 6 h |
| 5 | [05-introducao-modbus.md](05-introducao-modbus.md) | Filosofia, modelo de dados, function codes | 4 h |
| 6 | [06-modbus-rtu.md](06-modbus-rtu.md) | Modbus RTU: frame, CRC-16, timing | 8 h |
| 7 | [07-modbus-ascii.md](07-modbus-ascii.md) | Modbus ASCII: variante textual | 2 h |
| 8 | [08-fundamentos-tcp-ip.md](08-fundamentos-tcp-ip.md) | TCP/IP, sockets, portas | 6 h |
| 9 | [09-modbus-tcp.md](09-modbus-tcp.md) | Modbus TCP: MBAP, encapsulamento | 6 h |
| 10 | [10-praticas-visao-geral.md](../labs/10-praticas-visao-geral.md) | Visão geral das práticas | — |
| 11 | [11-pratica-em3p-easymodbus.md](../labs/11-pratica-em3p-easymodbus.md) | Prática 1: EM3P + EasyModbusTCP | 1.5 h |
| 12 | [12-pratica-em3p-python.md](../labs/12-pratica-em3p-python.md) | Prática 2: EM3P + Python | 1.5 h |
| 13 | [13-pratica-em3p-nodered.md](../labs/13-pratica-em3p-nodered.md) | Prática 3: EM3P + Node-RED | 2 h |
| 14 | [14-pratica-vfd7-easymodbus.md](../labs/14-pratica-vfd7-easymodbus.md) | Prática 4: VFD7 + EasyModbusTCP | 1.5 h |
| 15 | [15-pratica-vfd7-python.md](../labs/15-pratica-vfd7-python.md) | Prática 5: VFD7 + Python | 2 h |
| 16 | [16-pratica-vfd7-nodered.md](../labs/16-pratica-vfd7-nodered.md) | Prática 6: VFD7 + Node-RED | 2 h |
| 17 | [17-pratica-grupo-1-3clientes-1vfd.md](../labs/17-pratica-grupo-1-3clientes-1vfd.md) | Prática Grupo 1: 3 clientes / 1 VFD | 3 h |
| 18 | [18-pratica-grupo-2-1cliente-3vfds.md](../labs/18-pratica-grupo-2-1cliente-3vfds.md) | Prática Grupo 2: 1 cliente / 3 VFDs (orquestração) | 3 h |
| 19 | [19-pratica-grupo-3-3clientes-3vfds.md](../labs/19-pratica-grupo-3-3clientes-3vfds.md) | Prática Grupo 3: 3 clientes / 3 VFDs | 3 h |
| 20 | [20-pratica-grupo-4-mini-planta.md](../labs/20-pratica-grupo-4-mini-planta.md) | Prática Grupo 4: 2 VFDs + 1 medidor | 4 h |

---

## Estrutura Pedagógica

A disciplina foi desenhada como **uma jornada de camadas**, do mais físico (elétrons no fio) ao mais abstrato (integração SCADA):

```
   ┌─────────────────────────────────────┐
   │  Módulos 17-20: 4 práticas em grupo │  ← integração e coordenação
   ├─────────────────────────────────────┤
   │  Módulos 11-16: Práticas individuais│  ← consolidação por ferramenta
   ├─────────────────────────────────────┤
   │  Módulo 10: Visão geral das práticas│  ← orientação
   ├─────────────────────────────────────┤
   │  Módulo  9: Modbus TCP              │  ← objetivo principal
   ├─────────────────────────────────────┤
   │  Módulo  8: TCP/IP                  │
   ├─────────────────────────────────────┤
   │  Módulo  7: Modbus ASCII            │
   ├─────────────────────────────────────┤
   │  Módulo  6: Modbus RTU              │  ← coração do Modbus
   ├─────────────────────────────────────┤
   │  Módulo  5: Introdução ao Modbus    │
   ├─────────────────────────────────────┤
   │  Módulo  4: RS-485                  │
   ├─────────────────────────────────────┤
   │  Módulo  3: RS-232                  │
   ├─────────────────────────────────────┤
   │  Módulo  2: Comunicação serial      │
   ├─────────────────────────────────────┤
   │  Módulo  1: Por que comunicar?      │  ← motivação inicial
   └─────────────────────────────────────┘
```

**Princípio didático:** cada módulo **assume** o conteúdo dos módulos anteriores e **prepara** os subsequentes. Não pule etapas.

---

## Ferramentas Utilizadas

| Ferramenta | Função |
|------------|--------|
| **EasyModbusTCP** | Cliente Modbus para testes interativos |
| **Python + pymodbus** | Implementação programática de clientes e servidores |
| **Node-RED** | Middleware visual para dashboards e integração |
| **Wireshark** | Análise de tráfego de rede |
| **com0com** | Portas COM virtuais no Windows |
| **PuTTY / RealTerm** | Terminais seriais |
| **ModbusDeviceSIM** | Simulador proprietário (este repositório) |

---

## Equipamentos Simulados pelo ModbusDeviceSIM

A disciplina utiliza intensivamente nosso simulador **ModbusDeviceSIM** (versões Python desktop e Android):

- **MK-EM3P** — Medidor de energia trifásico (47 registradores de medição + 17 de configuração)
- **MK-VFD7** — Inversor de frequência / motor drive

Ambos seguem padrões realistas inspirados em equipamentos comerciais (Schneider PM5xxx, Carlo Gavazzi EM, ABB ACS580, Siemens G120).

---

## Para Quem Está Começando

Se você é o aluno e está abrindo este material pela primeira vez, **comece pelo [Módulo 1](01-introducao-comunicacoes-industriais.md)**. Cada módulo termina com:

- **Exercícios** (conceituais, cálculos, projetos)
- **Leitura recomendada** para a próxima aula
- **Síntese** dos pontos-chave

Não pule os exercícios. Eles existem porque **resolver problemas é como o conhecimento se solidifica**.

---

## Para Quem Vai Ensinar

Se você é instrutor e quer usar este material:

- O **Plano de Ensino** ([00-plano-de-ensino.md](00-plano-de-ensino.md)) traz a estrutura formal: ementa, objetivos, cronograma, avaliação.
- Os módulos podem ser **adaptados** para outros formatos (workshops, treinamentos corporativos).
- As práticas em [Módulo 10](../labs/10-praticas-visao-geral.md) podem ser usadas isoladamente.

Sinta-se à vontade para adaptar — apenas mantenha a atribuição.

---

## Licença e Atribuição

Este material é parte do projeto **ModbusDeviceSIM** e segue a licença do repositório principal.

**Autor:** Prof. Dênis Leite — Mekatronik — Advanced Engineering

---

## Bibliografia

A bibliografia completa está no [Plano de Ensino](00-plano-de-ensino.md#6-bibliografia).
