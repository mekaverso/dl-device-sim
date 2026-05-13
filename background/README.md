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
| 10 | [10-praticas-laboratorio.md](10-praticas-laboratorio.md) | 8 práticas de laboratório | 8 h |
| 11 | [11-projeto-integrador.md](11-projeto-integrador.md) | Projeto final | 2 h + extra |

---

## Estrutura Pedagógica

A disciplina foi desenhada como **uma jornada de camadas**, do mais físico (elétrons no fio) ao mais abstrato (integração SCADA):

```
   ┌─────────────────────────────────────┐
   │  Módulo 11: Projeto Integrador      │  ← integração total
   ├─────────────────────────────────────┤
   │  Módulo 10: Práticas com ferramentas│  ← consolidação
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
- As práticas em [Módulo 10](10-praticas-laboratorio.md) podem ser usadas isoladamente.

Sinta-se à vontade para adaptar — apenas mantenha a atribuição.

---

## Licença e Atribuição

Este material é parte do projeto **ModbusDeviceSIM** e segue a licença do repositório principal.

**Autor:** Prof. Dênis Leite — Mekatronik — Advanced Engineering

---

## Bibliografia

A bibliografia completa está no [Plano de Ensino](00-plano-de-ensino.md#6-bibliografia).
