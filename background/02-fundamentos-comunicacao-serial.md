# Módulo 2 — Fundamentos de Comunicação Serial Assíncrona

> *"Um bit de cada vez, com calma e disciplina."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Diferenciar comunicação serial e paralela e justificar a preferência industrial pela serial.
2. Descrever o funcionamento de uma UART e o formato de um frame serial assíncrono.
3. Calcular bit de paridade e detectar erros simples por paridade.
4. Diferenciar baud rate de bit rate, e simplex/half-duplex/full-duplex.
5. Estimar o tempo necessário para transmitir uma mensagem dada a taxa.

---

## 2.1 Paralelo vs. Serial

Imagine que você quer transmitir o byte `0b10110100` (= 0xB4 = 180) por um cabo.

### 2.1.1 Transmissão paralela

```
       ┌─────────────────────────┐
   D7 ─┤■                       ┌── 1
   D6 ─┤■                       ├── 0
   D5 ─┤■                       ├── 1
   D4 ─┤■        cabo de         ├── 1
   D3 ─┤■        8 fios          ├── 0
   D2 ─┤■                       ├── 1
   D1 ─┤■                       ├── 0
   D0 ─┤■                       └── 0
       └─────────────────────────┘
        Emissor               Receptor
```

Cada bit viaja por um fio dedicado, **simultaneamente**. Rápido, mas:

- **Custo:** 8 fios em vez de 1.
- **Skew:** sinais chegam levemente fora de fase em distâncias maiores (cross-talk).
- **Não escalável:** um byte exige 8 fios; transmitir 100 metros é caro.

### 2.1.2 Transmissão serial

```
       ┌──────────┐                   ┌──────────┐
       │ Buffer   │  ── um único ─►   │ Shift    │
       │ paralelo │     fio            │ register │
       └──────────┘                   └──────────┘
        Emissor                        Receptor

   Os bits saem em sequência, separados no tempo:

   tempo →   D0   D1   D2   D3   D4   D5   D6   D7
            (0)  (0)  (1)  (0)  (1)  (1)  (0)  (1)
```

**Apenas um fio para os dados.** Mais lento por natureza (cada bit consome um tempo), mas:

- **Barato:** menos cobre, menos isolação, menos conectores.
- **Robusto:** pode-se usar pares trançados para ganhar imunidade a ruído.
- **Distância:** dezenas a milhares de metros sem perda significativa.

> **Por que a indústria abandonou o paralelo?** Mesmo internamente nos computadores modernos, o paralelo deu lugar a **serial de alta velocidade**: PCI Express, SATA, USB, SAS — todos seriais. Vencer o skew custa mais caro do que aumentar a frequência de um único canal.

---

## 2.2 A UART

**UART** = *Universal Asynchronous Receiver/Transmitter*. É um circuito (hoje, um periférico embutido em quase todo microcontrolador) que faz a interface entre o **mundo paralelo do barramento de dados** e o **mundo serial do fio**.

```
   Microcontrolador                            Outro micro
   ┌─────────────────┐                       ┌─────────────────┐
   │  CPU            │                       │            CPU  │
   │   │ 8 bits      │                       │      8 bits│    │
   │   ▼             │                       │            ▼    │
   │  ┌───────────┐  │                       │  ┌───────────┐  │
   │  │   UART    │  │  TX ─────────────► RX │  │   UART    │  │
   │  │           │  │  RX ◄───────────── TX │  │           │  │
   │  │ paralelo  │  │       GND ──── GND    │  │ paralelo  │  │
   │  │ ↔ serial  │  │                       │  │ ↔ serial  │  │
   │  └───────────┘  │                       │  └───────────┘  │
   └─────────────────┘                       └─────────────────┘
```

A UART recebe um byte do barramento paralelo, o **serializa** (envia bit a bit pelo pino TX) e, na outra ponta, **deserializa** os bits recebidos no pino RX para reconstruir o byte.

### 2.2.1 Por que **assíncrono**?

Não há fio de **clock** entre as duas UARTs. Cada uma usa seu **próprio relógio interno**. Para que isso funcione, ambas devem:

1. **Concordar na taxa de transmissão** (baud rate).
2. **Reconhecer o início de cada byte** (start bit).
3. **Tolerar pequenas diferenças** de clock (até ~5 %).

Esse é o nome do jogo: comunicar **sem compartilhar o clock**.

---

## 2.3 Anatomia do Frame Serial

Um frame UART típico tem a seguinte estrutura:

```
   ─── linha idle (alto) ────┐
                             │
                          ┌──┐                              ┌──── alto
                          │  │ D0 D1 D2 D3 D4 D5 D6 D7 P    │
                          │  ├──┬──┬──┬──┬──┬──┬──┬──┬──┐ ──┘
                          │  │  │  │  │  │  │  │  │  │  │
                          └──┘                          └──┘
                          ↑                          ↑   ↑
                          │                          │   └── stop bit
                          │                          └────── parity (opcional)
                          └─── start bit (baixo)
```

| Campo       | Função                                                              |
|-------------|---------------------------------------------------------------------|
| Idle        | Linha em nível alto (lógico 1) quando não há transmissão            |
| Start bit   | Transição alto→baixo. Marca início de novo byte                     |
| Data bits   | Tipicamente 8 bits (LSB primeiro: D0, D1, …, D7)                    |
| Parity bit  | Opcional. Even, Odd, Mark, Space ou None                            |
| Stop bit(s) | 1 ou 2 bits em nível alto. Tempo mínimo de "silêncio"               |

### 2.3.1 Por que start bit é nível baixo e idle é alto?

Historicamente, a linha em nível alto significa "alimentada" — um cabo desconectado faria a linha cair para zero, indicando falha. Garantir que **idle = alto** facilita detectar:

- Cabo desconectado: linha em 0 contínuo.
- Início real de transmissão: transição 1→0 (start bit).

### 2.3.2 Os bits são transmitidos do **LSB para o MSB**

```
   Byte transmitido: 0xB4 = 0b10110100

   Ordem no fio:  D0 = 0    (LSB)
                  D1 = 0
                  D2 = 1
                  D3 = 0
                  D4 = 1
                  D5 = 1
                  D6 = 0
                  D7 = 1    (MSB)
```

**Atenção:** essa ordem é exclusiva da UART e dos bits **dentro do byte**. Quando estudarmos Modbus, veremos que a ordem **dos bytes** dentro do frame segue outra convenção (big-endian).

---

## 2.4 Bit de Paridade

A paridade é o **mecanismo mais simples de detecção de erro** que existe. Funciona assim:

### 2.4.1 Paridade par (Even)

Conta-se o número de **bits 1** no byte. Adiciona-se um bit extra (o bit de paridade) de forma que o **número total de bits 1** (incluindo o de paridade) seja **par**.

```
   Byte: 0xB4 = 0b10110100
   Quantos bits 1? → 4 (já é par)
   Bit de paridade par → 0
   Frame com paridade par: 0xB4 + 0 = 10110100 0
```

```
   Byte: 0x65 = 0b01100101
   Quantos bits 1? → 4 (par)
   Bit de paridade par → 0

   Byte: 0x67 = 0b01100111
   Quantos bits 1? → 5 (ímpar)
   Bit de paridade par → 1   ← força o total a ficar par
```

### 2.4.2 Paridade ímpar (Odd)

Análogo, mas o **total** de bits 1 deve ser **ímpar**.

### 2.4.3 Detectando um erro

Se um bit for invertido durante a transmissão (por ruído), o número de bits 1 muda em **uma unidade**. A paridade quebra.

```
   Original (par):    10110100 0   (4 bits 1 + 0 paridade = 4 = par) ✓
   Recebido com erro: 10100100 0   (3 bits 1 + 0 paridade = 3 = ímpar) ✗ ERRO
```

### 2.4.4 Limitações da paridade

- Detecta apenas **número ímpar** de bits invertidos. Se 2 bits forem invertidos, a paridade volta a "fechar" e o erro passa despercebido.
- Não detecta a **posição** do erro.
- **Não corrige** o erro, apenas avisa.

Por isso, em Modbus, além da paridade, existe um **CRC-16** (RTU) ou **LRC** (ASCII) para validação mais robusta do frame inteiro. Veremos esses cálculos em detalhes nos Módulos 6 e 7.

### 2.4.5 As cinco opções de paridade

| Tipo  | Bit de paridade                              | Notação típica |
|-------|----------------------------------------------|----------------|
| None  | Não há                                       | `N`            |
| Even  | Total de 1s (data + paridade) é par          | `E`            |
| Odd   | Total de 1s (data + paridade) é ímpar        | `O`            |
| Mark  | Sempre 1                                     | `M`            |
| Space | Sempre 0                                     | `S`            |

A configuração típica de uma porta serial é descrita como **8N1**, **8E1**, **8O1**, etc.:

- **8** = 8 bits de dados
- **N/E/O/M/S** = paridade
- **1** = 1 bit de parada

> **Em Modbus RTU**, o padrão é **8E1** (8 bits, paridade par, 1 stop bit) — quando há paridade. Quando não há paridade (`N`), o padrão é **8N2** (dois stop bits para manter o tamanho total de 11 bits por frame).

---

## 2.5 Taxa de Transmissão — Baud Rate vs. Bit Rate

### 2.5.1 Baud rate

**Baud rate** mede quantas **transições de símbolo por segundo** ocorrem no canal. A unidade é **baud** (Bd), em homenagem ao francês Émile Baudot.

Para UART simples, cada símbolo carrega **1 bit**, então:

> **Baud rate = bit rate** *(em UART convencional)*

### 2.5.2 Tabelas-padrão

As taxas mais comuns em sistemas industriais:

| Baud      | Tempo de 1 bit | Uso típico                           |
|-----------|----------------|--------------------------------------|
| 1200      | 833 µs         | Legado, modems antigos               |
| 2400      | 417 µs         | Sensores muito antigos               |
| 4800      | 208 µs         | HART, alguns medidores               |
| **9600**  | **104 µs**     | **Padrão industrial, default Modbus**|
| 19200     | 52 µs          | Modbus comum                         |
| 38400     | 26 µs          | Modbus mais rápido                   |
| 57600     | 17 µs          | Aplicações com volume                |
| 115200    | 8,7 µs         | Limite prático RS-485 em distância   |

> **Por que números "estranhos"?** São divisores binários de um clock-base de **1,8432 MHz**, frequência clássica de cristais para UART. 1.843.200 / 192 = 9.600.

### 2.5.3 Calculando o tempo de transmissão

**Quantos bits por byte?** Em 8E1: 1 start + 8 dados + 1 paridade + 1 stop = **11 bits**.

Em 8N1: 1 start + 8 dados + 1 stop = **10 bits**.

**Exemplo:** Quanto tempo leva transmitir 100 bytes em 9600 baud, 8E1?

```
   100 bytes × 11 bits/byte = 1100 bits
   1100 bits / 9600 bits/s ≈ 0,1146 s ≈ 115 ms
```

**Implicação prática:** uma rede Modbus RTU em 9600 baud com 30 escravos demora **alguns segundos** para varrer toda a rede. Por isso baud rates maiores e/ou Modbus TCP são preferíveis em redes grandes.

---

## 2.6 Modos de Transmissão: Simplex, Half-Duplex, Full-Duplex

### 2.6.1 Simplex

Comunicação em **uma única direção**.

```
   Emissor ──────────► Receptor
```

Exemplo: rádio AM. Não se aplica diretamente em controle industrial moderno.

### 2.6.2 Half-Duplex

Comunicação em **ambas as direções**, mas **uma de cada vez**. As estações precisam "tomar turno".

```
   Estação A ◄────────► Estação B
                ↑
            Mesmo canal,
            uma direção
            de cada vez
```

Exemplo: rádio walkie-talkie ("câmbio"). **RS-485** opera em half-duplex tipicamente. **Modbus RTU** é half-duplex: o mestre fala, o escravo responde, **nunca simultaneamente**.

### 2.6.3 Full-Duplex

Comunicação **simultânea** nas duas direções, em canais separados.

```
   Estação A  TX ────────► RX  Estação B
              RX ◄──────── TX
```

Exemplo: **RS-232** (TX e RX em fios separados), telefone, Ethernet moderna (par diferenciado em cada sentido).

| Modo        | Canais   | Simultaneidade | Exemplos                  |
|-------------|----------|----------------|---------------------------|
| Simplex     | 1        | Não            | Rádio AM/FM, TV broadcast |
| Half-Duplex | 1        | Não            | RS-485, walkie-talkie     |
| Full-Duplex | 2        | Sim            | RS-232, Ethernet, telefone|

---

## 2.7 Sincronia: Síncrono vs. Assíncrono

### 2.7.1 Comunicação síncrona

Existe um **fio de clock** separado, ou o clock é **embutido** no próprio sinal (por ex., manchester encoding).

```
   Dados ─►─►─►─►─►─►
   Clock ─┐_┌─┐_┌─┐_┌─┐_   ← cada borda diz "agora, este bit"
```

**Vantagens:** taxas altíssimas (Gbps), distâncias longas, alta confiabilidade temporal.

**Desvantagens:** mais cabos ou hardware mais complexo.

Exemplos: SPI, I²S, USB, Ethernet, HDMI.

### 2.7.2 Comunicação assíncrona

Sem clock compartilhado. Cada lado tem seu relógio. Sincroniza-se a cada byte usando o **start bit**.

```
   Dados ─────┐  D0 D1 D2 D3 D4 D5 D6 D7 P ┌───── idle
              │__│__│__│__│__│__│__│__│__│
              ↑   ↑                       ↑
              │   │ receptor amostra no   │
              │   │ centro de cada bit    │
              │   │ usando seu próprio    │
              │   │ clock interno         │
              │                           │
            start bit                   stop bit
```

A UART é assíncrona. Por isso:

- **Não há fio de clock** entre as UARTs.
- **A precisão dos cristais importa** — desvios maiores que ~5 % causam erros.
- **Cada byte é autocontido**: start, dados, parity, stop. Não há "fluxo contínuo".

> **Observação histórica:** o nome **UART** carrega o "A" de Assíncrono. Existem também USARTs (S de Síncrono) que suportam ambos os modos, mas a maioria das aplicações industriais usa o modo assíncrono.

---

## 2.8 Como o Receptor Lê os Bits — Oversampling

Receptores UART usam tipicamente **oversampling de 16×**: o relógio interno do receptor amostra a linha 16 vezes por bit. A amostragem ocorre **no centro do bit** (amostras 7, 8, 9), reduzindo a chance de capturar um valor durante a transição.

```
   Bit a transmitir:    ────────────────────────
                       Bit 0 →     Bit 1 →
   Linha:              _________   _________
   Amostras (16×):  ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                                ↑                  ↑
                          amostra centro      amostra centro
                          do bit 0            do bit 1
```

Essa estratégia tolera **desvios de relógio** de até **~5 %** entre emissor e receptor sem perder bits. Os cristais usados em UARTs (geralmente XTAL de 11,0592 MHz, 14,7456 MHz, 16 MHz) têm precisão de **±30 ppm**, muito melhor que o necessário.

---

## 2.9 Exemplo Completo: 8E1 a 9600 baud

Vamos enviar o caractere ASCII `'A'` (= 0x41 = 0b01000001).

**Configuração:** 8 bits de dados, paridade par, 1 stop bit, 9600 baud.

**Cálculo da paridade:**
- 0x41 = 0b**0**1000001
- Quantos bits 1? Dois (D0 e D6). Já é par.
- Bit de paridade par = **0**

**Sequência transmitida** (linha em alto = idle):

```
   Idle | Start | D0 D1 D2 D3 D4 D5 D6 D7 | Par | Stop | Idle
    1   |   0   |  1  0  0  0  0  0  1  0 |  0  |  1   |  1
```

Total: 11 bits.

**Duração total:** 11 × (1 / 9600) ≈ **1,146 ms**.

**Taxa efetiva de bytes:** 1 / 0,001146 ≈ **872 bytes/s** (com overhead de start/parity/stop).

> Note que **só 8 dos 11 bits transmitem dado útil**. A "eficiência" de uma UART 8E1 é **8/11 ≈ 73 %**. É o preço da simplicidade do esquema assíncrono.

---

## 2.10 Erros Comuns na Configuração de UART

| Sintoma                              | Causa provável                              |
|--------------------------------------|---------------------------------------------|
| Recebe lixo aparentemente aleatório  | Baud rate diferente entre as pontas         |
| Recebe os bits invertidos (bit 0 vira 1) | Problema de polaridade, RS-232 sem inversor |
| Funciona em curta distância e falha longe | Ruído elétrico; usar RS-485 em vez de RS-232 |
| Funciona com 1 byte, falha com sequência longa | Buffer insuficiente, sem controle de fluxo |
| Caracteres "saltam"                  | Stop bit incorreto (1 vs 2), ou frame errado |
| Recebe sempre 0xFF                   | TX desconectado, linha em alto              |
| Recebe sempre 0x00                   | RX em curto, ou pino flutuando              |

---

## 2.11 Exercícios

### Conceituais

1. Explique por que comunicação serial é preferível a paralela em distâncias industriais.
2. O que aconteceria se a UART do receptor estivesse configurada para 9600 baud, mas a UART do emissor estivesse em 4800 baud? Descreva qualitativamente o que o receptor "veria".
3. Em qual modo de duplex opera o Modbus RTU? Justifique pelo desenho elétrico do RS-485 (anteciparemos no Módulo 4).

### Cálculos

4. Qual o bit de paridade **ímpar** para o byte **0x6F**?
5. Calcule o tempo de transmissão de um frame Modbus RTU de **8 bytes** a **19200 baud**, configuração **8N1**.
6. Uma rede RS-485 em **9600 baud, 8E1** com **20 escravos** é varrida pelo mestre. Cada transação (request + resposta) totaliza, em média, **20 bytes**. Estime o tempo mínimo para varrer toda a rede (sem considerar timing de silêncio).

### Análise

7. Capture, com um osciloscópio (ou simule em software), a transmissão do caractere **'M'** em **8N1, 9600 baud**. Desenhe o sinal no tempo, marcando start, dados, stop e indicando o valor de cada bit.
8. Considere um receptor UART com oversampling de 16× e cristal com erro de **+3 %**. Após quantos bits ele provavelmente erra a amostragem por ter "atrasado demais" em relação ao emissor? Discuta.

### Aplicação

9. Você precisa configurar a UART de um sensor que documenta apenas "115200 baud, sem paridade". Qual configuração você deve usar: 8N1 ou 8N2? Justifique olhando o overhead total do frame.
10. **Pesquisa.** Procure um manual de um sensor industrial real (qualquer marca) e identifique a configuração serial padrão dele. Anote: baud rate, número de bits de dados, paridade, stop bits.

---

## 2.12 Leitura recomendada para a próxima aula

- Especificação **EIA/TIA-232-F** (overview)
- Revisar pinagem do conector **DB-9 e DB-25**
- Revisar conceitos de **tensão diferencial** e **modo comum** (será central no RS-485)

---

**Próximo módulo:** [03-padrao-rs232.md](03-padrao-rs232.md)
