# Módulo 3 — Padrão RS-232: O Clássico Indispensável

> *"Conhecer RS-232 é conhecer a raiz de tudo o que veio depois."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Descrever as características elétricas do padrão RS-232 (EIA/TIA-232-F).
2. Identificar a função dos pinos do conector DB-9 e DB-25.
3. Explicar handshaking de hardware e por que ele existe.
4. Reconhecer as limitações do RS-232 e justificar a migração para RS-485 em ambientes industriais.
5. Diagnosticar problemas comuns em conexões RS-232.

---

## 3.1 Origem e Contexto Histórico

O padrão **RS-232** (*Recommended Standard 232*) foi publicado pela **EIA** (*Electronic Industries Association*) em **1960**. Seu objetivo original: padronizar a interface entre **DTE** (*Data Terminal Equipment*, um terminal ou computador) e **DCE** (*Data Communication Equipment*, um modem).

```
   ┌─────────┐    RS-232    ┌────────┐   linha telefônica   ┌────────┐    RS-232   ┌─────────┐
   │ Terminal│──────────────│ Modem  │═══════════════════════│ Modem  │─────────────│ Terminal│
   │  (DTE)  │              │ (DCE)  │                       │ (DCE)  │             │  (DTE)  │
   └─────────┘              └────────┘                       └────────┘             └─────────┘
```

> **Pergunta retórica:** modems já não existem (na maior parte do mundo). Por que estudamos RS-232 em 2026?
>
> Porque o padrão **sobreviveu** ao seu propósito original. Foi adotado massivamente para conectar PCs a impressoras, mouses, scanners, plotters, e — crucialmente — para conectar PLCs, inversores de frequência, medidores e SCADAs. **Toda placa de PC tinha porta serial** até meados dos anos 2000. Os adaptadores **USB-RS232** mantêm o padrão vivo até hoje.

A versão atualmente referenciada é **TIA-232-F** (1997), substituindo a EIA-232-E.

---

## 3.2 Características Elétricas

### 3.2.1 Níveis de tensão

RS-232 é uma **interface single-ended** (não-diferencial). O sinal é medido em relação ao **terra (GND)**.

```
   Tensão no fio                          Lógica
   ────────────────────────────────────────────────
    +3 V a +15 V                          0  (SPACE)
   -15 V a -3 V                           1  (MARK)
   -3 V a +3 V                            indefinido
```

> **Atenção:** os níveis lógicos do RS-232 são **invertidos** em relação à lógica TTL/CMOS comum:
> - Linha em **alto positivo** (~+12 V) → lógico **0**
> - Linha em **alto negativo** (~−12 V) → lógico **1**
>
> Por isso, ao conectar um microcontrolador (que usa 0/3,3 V ou 0/5 V) a um cabo RS-232, é necessário um **driver/receiver** como o MAX232 que faz a inversão e o nível de tensão.

### 3.2.2 Por que tensões tão altas?

Quando o padrão foi criado, os transistores eram caros e ruidosos. Trabalhar com **amplitudes grandes** (até ~30 V de excursão pico-a-pico) proporcionava:

- **Alta imunidade a ruído**: ruído de 1–2 V não corrompia o sinal.
- **Compatibilidade com cabos longos** (até 15 m na especificação).
- **Facilidade para detectar conexão** (presença de tensão).

Em 1960, isso era uma vantagem. Hoje, é uma das limitações do padrão (consumo de potência, necessidade de fonte negativa, problemas com fontes simples 3,3 V).

### 3.2.3 Estados elétricos nomeados

Por herança da telegrafia, RS-232 usa nomes especiais para os estados elétricos:

| Estado | Tensão típica | Lógica | Origem do nome           |
|--------|---------------|--------|--------------------------|
| MARK   | ~−12 V        | 1      | "presença" no telégrafo  |
| SPACE  | ~+12 V        | 0      | "ausência" no telégrafo  |

Quando você vê documentação dizendo *"line goes to SPACE"*, traduza: a linha foi para tensão positiva, lógico 0.

### 3.2.4 Outras características elétricas

| Parâmetro                       | Valor                              |
|---------------------------------|------------------------------------|
| Impedância de carga             | 3–7 kΩ                             |
| Capacitância máxima da linha    | 2500 pF                            |
| Taxa de transmissão recomendada | ≤ 20 kbps (mas na prática 115200) |
| Distância recomendada           | até 15 m a 19200 baud              |
| Slew rate                       | ≤ 30 V/µs                          |

---

## 3.3 O Conector DB-9 (DE-9)

O conector RS-232 originalmente era o **DB-25** (25 pinos), mas a indústria simplificou para o **DE-9** (popularmente chamado de DB-9), com 9 pinos.

### 3.3.1 Pinagem DB-9 macho (DTE — visto de frente)

```
                                                       
              ┌────────────────────────────────┐    
              │    1   2   3   4   5            │    
              │     ●   ●   ●   ●   ●           │    
              │                                  │    
              │     ●   ●   ●   ●                │    
              │      6   7   8   9               │    
              └────────────────────────────────┘
```

### 3.3.2 Função de cada pino

| Pino | Sinal | Direção (DTE→DCE) | Função                                |
|------|-------|-------------------|---------------------------------------|
| 1    | DCD   | DCE → DTE         | Data Carrier Detect (modem detectou portadora) |
| 2    | RXD   | DCE → DTE         | Receive Data (DCE envia, DTE recebe)  |
| 3    | TXD   | DTE → DCE         | Transmit Data                         |
| 4    | DTR   | DTE → DCE         | Data Terminal Ready                   |
| 5    | GND   | comum             | Signal Ground                         |
| 6    | DSR   | DCE → DTE         | Data Set Ready                        |
| 7    | RTS   | DTE → DCE         | Request To Send                       |
| 8    | CTS   | DCE → DTE         | Clear To Send                         |
| 9    | RI    | DCE → DTE         | Ring Indicator (telefone tocando)     |

**Memorize bem:** **TXD, RXD, GND** — os três pinos absolutamente essenciais. Qualquer outra coisa é handshaking/sinalização auxiliar.

### 3.3.3 Pinagem em conectores fêmea

Atenção ao espelhamento: na fêmea, os pinos seguem a mesma numeração, mas a disposição física está espelhada porque você está olhando para o lado oposto do conector.

---

## 3.4 Handshaking

Handshaking é o conjunto de sinais auxiliares que permitem **controlar o fluxo** de dados entre DTE e DCE.

### 3.4.1 Handshaking de hardware

```
   DTE                                  DCE
   ┌─────────┐                       ┌─────────┐
   │   TXD ──┼──────────────────────►│ RXD     │
   │   RXD ◄─┼──────────────────────┤  TXD    │
   │   GND ──┼──────────────────────│  GND    │
   │         │                       │         │
   │   RTS ──┼──── "posso enviar?"──►│ CTS in  │
   │   CTS ◄─┼──── "pode enviar"  ───┤ RTS out │
   │         │                       │         │
   │   DTR ──┼──── "estou pronto" ──►│ DSR in  │
   │   DSR ◄─┼──── "estou pronto" ───┤ DTR out │
   │   DCD ◄─┼──── "carrier OK"  ────┤         │
   └─────────┘                       └─────────┘
```

| Sinal     | Função                                                          |
|-----------|------------------------------------------------------------------|
| **RTS**   | DTE diz: "tenho dados, posso transmitir?"                       |
| **CTS**   | DCE responde: "sim, pode transmitir"                            |
| **DTR**   | DTE diz: "estou ligado e pronto"                                |
| **DSR**   | DCE diz: "estou ligado e pronto"                                |
| **DCD**   | DCE diz: "estou recebendo portadora válida do outro lado"       |
| **RI**    | DCE diz: "o telefone está tocando" (legado de modems)           |

### 3.4.2 Handshaking de software (XON/XOFF)

Alternativamente, controle de fluxo pode ser feito **em-banda**, com caracteres especiais embutidos no próprio fluxo de dados:

- `XOFF` (0x13, Ctrl-S): "pare de enviar"
- `XON`  (0x11, Ctrl-Q): "pode continuar enviando"

Vantagem: precisa apenas dos 3 fios (TX, RX, GND). Desvantagem: usa **2 valores de byte** que não podem aparecer no fluxo de dados sem ambiguidade.

### 3.4.3 Sem handshaking

A maioria das aplicações industriais simples **não usa handshaking**. Os 3 fios mínimos (TX, RX, GND) bastam, com o fluxo controlado pela própria camada de protocolo (Modbus, por exemplo, sabe quando esperar resposta).

---

## 3.5 Cabos: Direto vs. Null Modem

### 3.5.1 Cabo direto

Conecta DTE a DCE (a função original):

```
   DTE (PC)                   DCE (modem)
   pino 2 RXD  ─────────────  pino 2 RXD
   pino 3 TXD  ─────────────  pino 3 TXD
   pino 5 GND  ─────────────  pino 5 GND
   pino 7 RTS  ─────────────  pino 7 RTS
   pino 8 CTS  ─────────────  pino 8 CTS
```

Pino 2 vai no pino 2, pino 3 no pino 3. Direto.

### 3.5.2 Cabo null modem

Conecta dois DTEs (dois PCs, ou PC a PLC). É necessário **cruzar TX/RX**:

```
   DTE A                       DTE B
   pino 2 RXD ◄──────────────  pino 3 TXD
   pino 3 TXD ──────────────►  pino 2 RXD
   pino 5 GND ──────────────  pino 5 GND
   pino 7 RTS ──────────────►  pino 8 CTS
   pino 8 CTS ◄──────────────  pino 7 RTS
   pino 4 DTR ──────────────►  pino 6 DSR + pino 1 DCD
   pino 6 DSR + pino 1 DCD ◄─  pino 4 DTR
```

**Memorize:** TX de um vai em RX do outro, e RTS de um vai em CTS do outro.

> **Pegadinha de laboratório:** ao tentar conectar dois PCs via RS-232 com um **cabo direto**, **nada funciona**. Os TXDs ficam "conversando entre si" e ninguém escuta. Use **cabo null modem** ou faça um adaptador cruzado.

---

## 3.6 Limitações do RS-232

### 3.6.1 Distância e taxa

A relação **distância × taxa** é restritiva:

| Baud      | Distância máxima recomendada |
|-----------|------------------------------|
| 9600      | ≈ 15 m                       |
| 38400     | ≈ 3 m                        |
| 115200    | ≈ 1 m                        |

A causa é a **capacitância acumulada** do cabo, que limita o slew rate. Cabos longos "borram" as transições de bit.

### 3.6.2 Single-ended, sensível a ruído

A medição em relação ao GND torna o RS-232 vulnerável a:

- **Diferença de potencial entre terras** (quando os dois dispositivos têm fontes diferentes)
- **Ruído eletromagnético** acoplado no fio
- **Surtos** de alimentação

### 3.6.3 Ponto-a-ponto

RS-232 é estritamente **um para um**. Não há topologia multidrop. Se você tem 10 sensores para ligar, precisa de 10 portas seriais (ou multiplexadores).

### 3.6.4 Comprimento mecânico

Os conectores DB-9 são **frágeis** para ambiente industrial: sem proteção contra água/poeira (IP), sem trava robusta, propensos a desconexão.

### 3.6.5 Tensões fora do padrão TTL

Microcontroladores trabalham em 0/3,3 V ou 0/5 V. RS-232 trabalha em ±12 V. Necessário **chip conversor** (MAX232, MAX3232, SP232) que gera as tensões negativas internamente via charge pump.

---

## 3.7 Adaptadores USB → RS-232

Como PCs modernos raramente têm porta serial nativa, são onipresentes os adaptadores **USB → RS-232**. Eles aparecem no sistema operacional como uma **porta COM virtual** (`COM3`, `COM4`, etc. no Windows; `/dev/ttyUSB0` no Linux).

Chips populares:

- **FTDI FT232R** — referência, drivers excelentes, mais caro
- **Prolific PL2303** — comum, drivers atualizados (versões antigas têm bugs no Windows 10+)
- **Silicon Labs CP2102** — boa relação custo/qualidade
- **CH340/CH341** — barato, comum em clones de Arduino

> **Cuidado com chips falsificados:** FTDIs falsificados são comuns em conversores baratos. O fabricante chegou a publicar drivers que "tijolavam" chips falsos. Em ambiente acadêmico, prefira FT232R originais ou CP210x.

---

## 3.8 Diagnóstico de Problemas

| Sintoma                                | Possíveis causas                                       |
|----------------------------------------|--------------------------------------------------------|
| Não aparece porta COM no PC            | Driver não instalado, cabo USB com defeito             |
| Porta COM aparece, mas nada se comunica| Cabo direto vs null modem, pinagem incorreta           |
| Caracteres "estranhos"                 | Baud rate, paridade ou stop bits incorretos            |
| Funciona até X bytes, depois trava     | Handshaking necessário; ative RTS/CTS                  |
| Erros aleatórios em ambiente industrial| Ruído elétrico; mude para RS-485                       |
| Distância > 15 m, falhas               | Limite de capacitância; reduza baud ou use RS-485      |
| Tensões diferentes (ex.: -3 V e +12 V) | Conversor TTL incompleto, falta fonte negativa         |

### 3.8.1 Ferramenta indispensável: loopback

Para testar se uma porta RS-232 funciona, faça um **loopback**:

```
   No DB-9 do PC:
   pino 2 (RXD) ─┐
                  │  curto-circuito
   pino 3 (TXD) ─┘
```

Qualquer caractere enviado deve voltar instantaneamente. Se não voltar, a porta está com defeito.

---

## 3.9 RS-232 e Modbus

O Modbus **pode** funcionar sobre RS-232, mas com **uma única limitação importante**: somente em modo **ponto-a-ponto**. Um mestre, um escravo. Para redes com múltiplos escravos, RS-485 é mandatório.

Aplicações típicas de Modbus sobre RS-232:

- Conectar **um inversor** ou **um medidor** ao computador para parametrização
- **Gateways** Modbus RTU ↔ Modbus TCP
- Ligação direta entre um **CLP e um HMI**

> A combinação **Modbus RTU + RS-232** é raríssima em redes de produção. **Modbus RTU + RS-485** é o padrão de fato.

---

## 3.10 Exercícios

### Conceituais

1. Por que o RS-232 usa lógica **invertida** em relação a TTL?
2. Explique a diferença entre DTE e DCE. Em qual categoria você classificaria um PC, um CLP, um modem, um inversor de frequência?
3. Por que o cabo entre dois PCs precisa ser **null modem**? O que aconteceria com um cabo direto?

### Análise

4. Considere a transmissão de 1024 bytes (1 KiB) por RS-232 em 9600 baud, 8N1. Quanto tempo leva?
5. Você precisa conectar um sensor a 50 metros de distância em 9600 baud. Discuta a viabilidade de usar RS-232 nessa aplicação.
6. Em um cabo RS-232 com fluxo de bytes incessante, vocé observa que após aproximadamente 30 segundos a comunicação "trava" e retoma sozinha alguns segundos depois. Diagnóstico provável?

### Prática

7. Identifique o chip conversor TTL-RS232 em uma placa de microcontrolador (ex.: MAX232). Verifique no datasheet a faixa de tensão de saída.
8. **Em laboratório:** monte um loopback com um conector DB-9. Use o terminal serial do PC para enviar caracteres e confirmar o eco. Documente.
9. **Pesquisa:** procure um conversor USB-RS232 comercial. Identifique o chip usado. Anote o modelo do CI e a corrente de operação típica.

### Projeto

10. Desenhe o esquema elétrico mínimo (TX, RX, GND) para conectar dois Arduinos via RS-232, considerando que os Arduinos têm UART TTL (5 V) e que cada Arduino precisa de um MAX232 entre o pino TX/RX TTL e o conector DB-9.

---

## 3.11 Leitura recomendada para a próxima aula

- Especificação **TIA/EIA-485-A** (overview)
- Revisar **amplificador diferencial**, **modo comum** e **modo diferencial**
- Pesquisar **terminadores de linha** e o efeito de **reflexões em linhas de transmissão**

---

**Próximo módulo:** [04-padrao-rs485.md](04-padrao-rs485.md)
