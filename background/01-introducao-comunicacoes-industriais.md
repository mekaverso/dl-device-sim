# Módulo 1 — Introdução às Comunicações Industriais

> *"Antes de comunicar, é preciso entender por que comunicar."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Identificar a motivação para a existência de protocolos de comunicação na indústria.
2. Distinguir sinais analógicos de sinais digitais em sistemas industriais.
3. Compreender a evolução histórica das comunicações industriais.
4. Posicionar o Modbus dentro do contexto dos protocolos industriais modernos.

---

## 1.1 O Problema Industrial

Imagine uma fábrica de cimento. Ela possui:

- Centenas de **sensores** (termopares, pressão, vazão, nível, vibração)
- Dezenas de **atuadores** (válvulas, motores, contatores)
- **Controladores Lógicos Programáveis (CLPs)** distribuídos pela planta
- Um **sistema supervisório (SCADA)** numa sala de controle
- Possivelmente um **ERP** no escritório administrativo

**A pergunta fundamental:** como esses elementos trocam informação?

### 1.1.1 A solução pré-histórica: fios paralelos

Até os anos 1970, cada sensor era ligado por um par de fios ao seu painel de controle. Um sensor de temperatura analógico gerava um sinal de **4–20 mA** ou **0–10 V** que era levado até um indicador ou ao bloco de entrada de um controlador.

```
   Termopar
      │
      │  cabo blindado, dezenas de metros
      │
      ▼
   Conversor 4–20 mA
      │
      │  par de fios
      │
      ▼
   Painel de controle (indicador, registrador, controlador)
```

**Problemas dessa abordagem:**

| Problema                        | Consequência                                              |
|---------------------------------|-----------------------------------------------------------|
| Um par de fios por variável     | Painéis gigantes, centenas de cabos                       |
| Sensibilidade a ruído           | Necessidade de cabos blindados e aterramento cuidadoso    |
| Sem diagnóstico                 | Um cabo rompido só era detectado pelo operador            |
| Não escalável                   | Adicionar um sensor exigia passar mais cabo               |
| Sem identificação               | O sinal era "anônimo"; precisava ser etiquetado no painel |

### 1.1.2 A solução moderna: rede digital

Com a evolução da microeletrônica nos anos 1970–1980, sensores e atuadores passaram a ter **microprocessadores embarcados**. Tornou-se possível **digitalizar a medição na fonte** e transmitir os dados através de uma **rede compartilhada**.

```
   Sensor inteligente A          Sensor B          Atuador C
        │                           │                  │
        └──────┬────────────────────┴──────────────────┘
               │
               │   Barramento serial (RS-485) ou Ethernet
               │
               ▼
        Controlador / Supervisor
```

**Benefícios:**

- Centenas de variáveis num único par de fios (ou cabo Ethernet)
- **Diagnóstico:** o protocolo sabe quem responde e quem está mudo
- **Bidirecional:** o controlador também escreve nos dispositivos (setpoints, comandos)
- **Padronizado:** qualquer fabricante que siga o padrão se conecta
- **Escalável:** adicionar um nó é só configurar um endereço

---

## 1.2 Sinais Analógicos vs. Digitais

Antes de comunicação digital, predominaram dois padrões de sinalização analógica:

### 1.2.1 Loop de corrente 4–20 mA

- Faixa: 4 mA = mínimo da grandeza, 20 mA = máximo
- **Por que corrente e não tensão?** Imunidade a ruído e queda de tensão no cabo. A mesma corrente passa em todo o circuito, independente da impedância do cabo.
- **Por que 4 mA mínimo (e não 0 mA)?** Para detectar cabo rompido: se a corrente for 0, o cabo foi rompido. Se for 4 mA, está OK.
- Distância: até centenas de metros
- Limitação: **um sinal por par de fios**

### 1.2.2 Tensão 0–10 V

- Mais simples, mais barato
- Sensível a queda de tensão no cabo
- Limitação a distâncias curtas (poucos metros)
- Hoje raro em ambientes industriais sérios; mais comum em prediais e laboratórios

### 1.2.3 Sinalização digital

A grande mudança conceitual é que **o sinal deixa de ser proporcional à grandeza física** e passa a ser um **fluxo de bits que representa um número**. Esse número, por sua vez, pode ser interpretado como temperatura, pressão, etc.

```
Analógico:   4 mA ──────────► 0 °C
            12 mA ──────────► 50 °C
            20 mA ──────────► 100 °C
             (relação linear contínua entre corrente e temperatura)

Digital:    0x0000 ──────────► 0 °C
            0x0064 ──────────► 100 °C  (decimal 100, escala = 1 °C/unidade)
            0xFFFF ──────────► fora de faixa
             (números codificados em bits, transmitidos por um protocolo)
```

**Vantagens da abordagem digital:**

- Precisão **independente da distância**
- Capacidade de transmitir múltiplas grandezas pelo mesmo cabo
- Possibilidade de transmitir **metadados** (unidade, escala, status, alarmes)
- Diagnóstico embutido (checksum, timeout, endereço)

---

## 1.3 Pirâmide da Automação

Historicamente, organizou-se a comunicação industrial em níveis hierárquicos — a célebre **Pirâmide de Automação**:

```
                    ╔═════════════╗
                    ║     ERP     ║    Nível corporativo (anos/meses)
                    ╠═════════════╣
                    ║    MES      ║    Nível de manufatura (dias/horas)
                    ╠═════════════╣
                    ║   SCADA     ║    Supervisão (segundos/minutos)
                    ╠═════════════╣
                    ║   CLP/DCS   ║    Controle (milissegundos)
                    ╠═════════════╣
                    ║   Campo     ║    Sensores e atuadores (microssegundos)
                    ╚═════════════╝
```

Cada nível tem **requisitos diferentes** de comunicação:

| Nível        | Requisito principal                          | Protocolos típicos              |
|--------------|----------------------------------------------|---------------------------------|
| Campo        | Determinístico, tempo real, baixa latência   | HART, Foundation Fieldbus, IO-Link |
| Controle     | Confiabilidade, ciclo curto                  | Profibus, **Modbus RTU/TCP**, EtherCAT |
| Supervisão   | Volume de dados, integração                  | **Modbus TCP**, OPC, MQTT       |
| Manufatura   | Histórico, qualidade                         | SQL, OPC UA, REST APIs          |
| Corporativo  | Decisão estratégica                          | HTTP/HTTPS, EDI, SAP            |

> **Onde o Modbus se encaixa?** Modbus é versátil: existe no nível de campo (RTU) e no nível de supervisão (TCP). É um dos protocolos com **maior amplitude vertical** na pirâmide.

> **Observação contemporânea:** essa pirâmide está se diluindo com a chegada do conceito de **Indústria 4.0**, onde sensores conversam diretamente com a nuvem. Mas o modelo segue útil como referência conceitual.

---

## 1.4 Breve Histórico das Comunicações Industriais

| Década | Marco                                                              |
|--------|--------------------------------------------------------------------|
| 1960   | Sinais analógicos 4–20 mA dominam a indústria                      |
| 1968   | Modicon cria o **primeiro CLP** (model 084)                        |
| 1979   | Modicon publica o **Modbus** — primeiro protocolo serial industrial aberto |
| 1985   | Padrão **RS-485** (TIA/EIA-485) é ratificado                       |
| 1989   | Profibus é lançado pela Siemens                                    |
| 1996   | **Ethernet/IP** (Rockwell) e **Modbus TCP** (Schneider) emergem    |
| 2003   | OPC UA é proposto                                                  |
| 2010s  | MQTT, AMQP e protocolos IoT ganham espaço                          |
| 2020s  | TSN (Time-Sensitive Networking), OPC UA over TSN, **Modbus Secure** |

> O Modbus, criado em **1979**, é mais antigo que a maioria dos alunos desta disciplina, mas **continua sendo um dos protocolos industriais mais usados no mundo**. Por quê?
>
> 1. **Aberto:** especificação pública desde sempre
> 2. **Simples:** implementação trivial em qualquer microcontrolador
> 3. **Suficiente:** atende 80 % dos casos de uso industriais
> 4. **Onipresente:** equipamento legado herdado por gerações de plantas

---

## 1.5 Por Que Estudar Modbus em 2026?

Há quem diga que Modbus é "antigo demais". A realidade industrial diz o contrário:

- **Inversores de frequência**: WEG, Schneider, ABB, Siemens, Danfoss — todos suportam Modbus.
- **Medidores de energia**: virtualmente todos os medidores industriais falam Modbus.
- **CLPs**: todos suportam Modbus como protocolo secundário, muitos como primário.
- **HMIs e SCADAs**: todos suportam Modbus para leitura/escrita de tags.
- **IoT industrial**: gateways Modbus → MQTT, OPC UA são ubíquos.

> **Insight do professor:** entender Modbus é entender **a lógica comum** por trás de protocolos industriais. Quem domina Modbus aprende Profibus, EtherNet/IP e OPC UA em uma fração do tempo, pois os conceitos de **endereçamento, function codes, modelo de dados** são análogos.

---

## 1.6 Visão Geral da Disciplina

A jornada que iniciamos é construída em camadas, do mais físico ao mais abstrato:

```
   ┌─────────────────────────────────┐
   │  Modbus TCP (rede Ethernet)     │  ← onde queremos chegar
   ├─────────────────────────────────┤
   │  Modbus RTU/ASCII (serial)      │
   ├─────────────────────────────────┤
   │  Padrões físicos (RS-232/485)   │
   ├─────────────────────────────────┤
   │  Comunicação serial (UART)      │
   ├─────────────────────────────────┤
   │  Bits, frames, paridade         │  ← onde começamos
   └─────────────────────────────────┘
```

Cada camada é construída sobre a anterior. **Não pule etapas** — entender por que existe um bit de paridade vai poupá-lo de horas de debug futuro.

---

## 1.7 Exercícios

1. **Conceitual.** Explique, com suas próprias palavras, por que a sinalização 4–20 mA usa 4 mA como valor mínimo em vez de 0 mA.

2. **Comparação.** Considere uma sala de controle com **80 sensores de temperatura** distribuídos numa área de 500 m². Compare quantitativamente (cabeamento, painel, custo de instalação) duas alternativas:
   - (a) Cada sensor com par de fios 4–20 mA até um painel central.
   - (b) Sensores Modbus em rede RS-485 conectados ao mesmo painel.

3. **Pesquisa.** Identifique três equipamentos industriais reais (com marca/modelo) que utilizem Modbus como protocolo de comunicação. Para cada um, indique: tipo de Modbus (RTU/TCP), porta padrão, e função do equipamento na indústria.

4. **Reflexão.** Por que um protocolo criado em 1979 ainda é amplamente usado em 2026? Que características arquiteturais explicam essa longevidade?

5. **Localização na pirâmide.** Indique em qual(is) nível(is) da pirâmide de automação você esperaria encontrar:
   - (a) Modbus RTU
   - (b) Modbus TCP
   - (c) MQTT
   - (d) OPC UA
   - (e) HART

---

## 1.8 Leitura recomendada para a próxima aula

- [https://modbus.org/about_us.php](https://modbus.org/about_us.php) — história oficial
- Revisar o conceito de **número binário**, **hexadecimal** e **conversão entre bases**
- Revisar **álgebra booleana** (AND, OR, XOR) — será usada no cálculo de CRC

---

**Próximo módulo:** [02-fundamentos-comunicacao-serial.md](02-fundamentos-comunicacao-serial.md)
