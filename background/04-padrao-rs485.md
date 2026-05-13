# Módulo 4 — Padrão RS-485: Robustez Industrial

> *"Se o RS-232 é o utilitário, o RS-485 é o caminhão de carga da automação."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Explicar o princípio de **sinalização diferencial** e justificar sua imunidade a ruído.
2. Calcular tensões diferencial e de modo comum em uma linha RS-485.
3. Descrever a topologia **multidrop** e o papel da terminação e polarização.
4. Diferenciar **RS-485** (half-duplex, 2 fios) de **RS-422** (full-duplex, 4 fios).
5. Projetar uma rede RS-485 funcional, escolhendo cabo, terminadores e número máximo de nós.

---

## 4.1 A Limitação Fundamental do RS-232

O RS-232 falha em ambientes industriais por **três motivos**:

1. **Single-ended** — mede tensão contra GND, vulnerável a ruído e diferença de potencial entre terras.
2. **Ponto-a-ponto** — não permite múltiplos dispositivos.
3. **Distância curta** — até 15 m em 9600 baud.

O RS-485 resolve **os três problemas** com uma única ideia central: **sinalização diferencial**.

---

## 4.2 Sinalização Diferencial: A Grande Ideia

Em vez de transmitir o sinal em **um fio contra GND**, o RS-485 usa **dois fios** que carregam o mesmo sinal em **fase oposta**. O receptor mede a **diferença entre eles**, não o valor absoluto.

```
   Lógica 1:
      Fio A:  ━━━━━━━━━━━━ +3 V
      Fio B:  ____________  0 V        diferença: A − B = +3 V

   Lógica 0:
      Fio A:  ____________  0 V
      Fio B:  ━━━━━━━━━━━━ +3 V        diferença: A − B = −3 V
```

> O receptor RS-485 detecta:
> - **(A − B) > +0,2 V** → lógico **1** (representado como **MARK** ou *OFF*)
> - **(A − B) < −0,2 V** → lógico **0** (representado como **SPACE** ou *ON*)
>
> Os fios A e B também são chamados de **D+** e **D−**, ou ainda **TR+** e **TR−**, dependendo do fabricante.

### 4.2.1 Por que diferencial rejeita ruído?

Imagine que um pulso de ruído eletromagnético (de um motor, por exemplo) acopla **+2 V** em ambos os fios A e B simultaneamente — afinal, eles correm juntos no mesmo cabo:

```
   Lógica 1 com ruído:
      Fio A:  ━━━━━━━━━━━━ +3 V + 2 V = +5 V
      Fio B:  ____________  0 V + 2 V = +2 V
                                     diferença: A − B = +3 V  ✓ continua lógico 1
```

O ruído **se cancela** na subtração. Isso é chamado de **rejeição de modo comum** (*Common-Mode Rejection*, CMR), e é o **superpoder** do RS-485.

### 4.2.2 Modo comum vs. modo diferencial

| Conceito          | Definição                                          |
|-------------------|----------------------------------------------------|
| Tensão diferencial | (V_A − V_B) — carrega o **sinal útil**            |
| Tensão de modo comum | (V_A + V_B)/2 — qualquer "offset" igual em ambos os fios |

RS-485 tolera modos comuns de até **±7 V** (mais alguns volts em chips modernos como o MAX485, que aceitam até ±15 V). É o que permite operar em ambientes com diferentes potenciais de terra.

### 4.2.3 Cabo: Par Trançado

Para que o ruído acople **igualmente** em ambos os fios, eles precisam **percorrer o mesmo caminho físico**. A solução: **par trançado**. Os dois fios giram em torno um do outro, dezenas de vezes por metro, garantindo que qualquer indução EM atinja os dois lados igualmente.

```
   Sem trançamento:
                Ruído
                  ↓↓↓
   Fio A  ─────────────────────  ← ruído acopla mais aqui
   Fio B  ─────────────────────  ← ruído acopla menos aqui
                                   (rejeição falha)

   Com trançamento:
   Fio A  ◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯
                            ← ruído acopla igualmente em A e B
   Fio B  ●●●●●●●●●●●●●●●     em cada volta, a polaridade inverte
                              e a média ao longo do cabo é zero
```

**Pequena regra prática:** quanto mais trançado o cabo, melhor o desempenho. **Cabo UTP cat 5e/6 funciona excelentemente para RS-485** — não precisa ser "cabo industrial caro" para muitas aplicações.

---

## 4.3 Especificações Elétricas (TIA/EIA-485-A)

| Parâmetro                          | Valor                                        |
|------------------------------------|----------------------------------------------|
| Tensão diferencial mínima (TX)     | ±1,5 V (típico ±2 V)                         |
| Tensão diferencial mínima (RX)     | ±200 mV (ou seja, é muito tolerante!)        |
| Faixa de modo comum                | −7 V a +12 V                                 |
| Impedância de saída                | mínima de 60 Ω (carga combinada)             |
| Impedância de linha (cabo)         | tipicamente 120 Ω                            |
| Número máximo de nós (drivers/receptores) | 32 cargas-padrão (mais com chips fracionários) |
| Distância máxima                   | 1200 m em 100 kbps; menos em taxas maiores   |
| Taxa máxima                        | 10 Mbps (em distâncias curtas)               |

### 4.3.1 Distância × Taxa (figura clássica)

```
   Distância (m)
   ▲
   1200 ┤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╲
        │                              ╲
    600 ┤                                ╲
        │                                  ╲
    300 ┤                                    ╲
        │                                      ╲
    100 ┤                                        ╲
        │                                          ╲
     30 ┤                                            ╲
        │                                              ╲
      0 └─────────┬─────────┬─────────┬─────────┬───────╲────► Taxa
              100 k     1 M       2 M      5 M      10 M  (bps)
```

Em **9600 baud**, alcança-se confortavelmente 1200 m. Em **115200 baud**, espere ~400 m.

---

## 4.4 Topologia Multidrop

O RS-485 permite **múltiplos dispositivos** compartilharem o mesmo par de fios — eis o que o torna ideal para redes industriais:

```
                         A    B
   Mestre        ┌───┐   │    │
   (RS-485 TX)   │   ├───┤    ├───── ... ──────┐
                 └───┘   │    │                 │
                         │    │                 │
                       ┌─┴─┐ ┌─┴─┐ ┌─┴─┐    ┌─┴─┐
                       │Esc│ │Esc│ │Esc│    │ Rt│  ← terminação 120 Ω
                       │ 1 │ │ 2 │ │ 3 │    └───┘
                       └───┘ └───┘ └───┘
```

> Cada **escravo** "pendura-se" nos dois fios A e B. Em qualquer instante, apenas **um dispositivo transmite** (modo half-duplex). Os demais ficam em modo de recepção (alta impedância na linha de transmissão).

### 4.4.1 Por que half-duplex?

Como **todos compartilham o mesmo par** de fios, se duas estações falassem ao mesmo tempo, o resultado seria **lixo** (colisão). Por isso o RS-485 (2 fios) é **half-duplex**: regra de turno gerenciada pelo protocolo de camada superior (no caso do Modbus, o mestre coordena).

Existe a variante **RS-422** que usa **4 fios** (um par dedicado para cada direção): full-duplex. Menos comum em redes Modbus, mais usado em transmissões dedicadas ponto-a-ponto longas.

### 4.4.2 Endereçamento — quem fala, quem responde?

A camada elétrica RS-485 **não sabe nada de endereços**. Tudo que ela faz é colocar bits no fio. **O protocolo da camada acima** (Modbus, neste caso) é que carrega o **endereço do escravo** no primeiro byte do frame. Cada escravo verifica:

- Se o endereço do frame **coincide com o meu** → responde.
- Caso contrário → ignora.

Esse esquema funciona porque **todos os escravos recebem todos os frames** no fio. Eles apenas filtram pelo endereço.

---

## 4.5 Terminação e Polarização

Dois detalhes elétricos que **fazem a diferença** entre uma rede funcional e uma "louca":

### 4.5.1 Terminação

Cabos longos comportam-se como **linhas de transmissão**. Se a impedância na ponta não casar com a impedância do cabo (120 Ω), o sinal **reflete** de volta, criando ecos e corrompendo a comunicação — especialmente em taxas altas.

**Solução:** colocar um resistor de **120 Ω** em **cada extremidade** da rede:

```
         Mestre        Esc 1   Esc 2   Esc 3        Esc N
         (no início    │       │       │              │
          da linha)    │       │       │              │
              │        │       │       │              │
   120 Ω ───┬─┴────────┴───────┴───────┴───── ... ────┴───┬─── 120 Ω
            │                                              │
            └──────────  par trançado A/B  ────────────────┘
```

**Cuidado:**
- Os terminadores ficam **nas extremidades**, **não nos nós intermediários**.
- Coloque **apenas dois** terminadores na rede (um em cada ponta).
- Muitos dispositivos têm um **jumper interno** para ativar/desativar a terminação.

### 4.5.2 Polarização (Bias)

Quando **nenhum** dispositivo está transmitindo, a linha fica "flutuando" — sem nível bem definido. Ruído pode fazer o receptor "ouvir" bits falsos.

**Solução:** resistores de **bias** que forçam a linha para um estado conhecido (idle = lógico 1):

```
   +5 V ────[680 Ω]─── A   (puxa A para cima)
                       │
                       │   par trançado
                       │
   GND  ────[680 Ω]─── B   (puxa B para baixo)
```

Esses resistores ficam **geralmente no mestre** ou em um dispositivo central. Sem eles, em redes longas com baud rates altos, pode haver **erros intermitentes** que enlouquecem o pessoal de manutenção.

> **Sintoma clássico de falta de bias:** rede funciona quando há tráfego, mas dá erro logo após período de silêncio.

---

## 4.6 Topologia: O que Fazer e o que Evitar

### 4.6.1 Correta: bus linear

```
   Mestre ─┬──────────────────────┬─────────────────┬──── 120 Ω
            │                       │                  │
          Esc1                    Esc2               EscN
```

Cada nó "pendura" em um único cabo. As **derivações (stubs)** devem ser **muito curtas** (idealmente < 0,3 m).

### 4.6.2 Errada: estrela

```
              Mestre
                │
                │ ← cabo longo
                │
              ┌─┴─┐
              │   │
          ┌───┘   └───┐
          │           │
        Esc1        Esc2
```

**Não funciona** bem em RS-485 — múltiplas reflexões, problemas de terminação.

### 4.6.3 Errada: árvore com stubs longos

```
   Mestre ──┬─────────────────┬──── 120 Ω
            │                  │
            │                  │
            ▼ stub             ▼ stub
         (2 metros)         (3 metros)  ← REFLEXÕES!
            │                  │
          Esc1               Esc2
```

Stubs longos criam reflexões. Mantenha sempre **curtas** (centímetros).

---

## 4.7 Os Chips Drivers Mais Comuns

| Chip       | Característica principal                        |
|------------|--------------------------------------------------|
| MAX485     | O clássico. 32 nós, ±7 V modo comum             |
| MAX487     | Baixo consumo, 128 nós                          |
| MAX3485    | Igual ao MAX485, mas 3,3 V                      |
| MAX13487   | Auto-direção (não precisa do pino DE)           |
| ADM2483    | Isolação galvânica integrada                    |
| LTC2862    | Modo comum ±60 V (super-robusto)                |

### 4.7.1 Pinagem clássica (MAX485)

```
              ┌──────────────┐
       RO ──◄│ 1          8 │── Vcc
       /RE ─►│ 2          7 │── B  (Data−)
       DE  ─►│ 3          6 │── A  (Data+)
       DI  ─►│ 4          5 │── GND
              └──────────────┘
```

- **RO** (Receiver Output): saída de dados recebidos para o microcontrolador
- **/RE** (Receiver Enable, ativo baixo): habilita o receptor
- **DE** (Driver Enable, ativo alto): habilita o transmissor
- **DI** (Driver Input): dados a transmitir, vindos do microcontrolador

**Como falar:** colocar `DE=1` e `/RE=1` (transmitindo, recepção desligada).
**Como escutar:** colocar `DE=0` e `/RE=0` (recebendo, transmissão em alta impedância).

> **Pegadinha:** se você esquecer de desligar `DE` após transmitir, **trava a rede**: ninguém mais consegue falar. Em microcontroladores, o controle de `DE` é tipicamente automatizado pelo driver UART/RS-485.

---

## 4.8 Aterramento e Isolação Galvânica

### 4.8.1 O problema dos terras desiguais

Em uma planta industrial, dispositivos podem estar em diferentes "ilhas elétricas" — quadros separados, fontes diferentes, conduítes longos. A diferença de potencial entre os terras pode chegar a **dezenas de volts**, especialmente durante surtos.

O RS-485 tolera ±7 V em chips clássicos, mas em ambientes brutos isso pode não bastar.

### 4.8.2 Soluções

1. **Conectar GND comum**: usar um terceiro fio entre os dispositivos (referência comum). Comum em RS-485 industrial — chama-se "RS-485 a 3 fios" (A, B, GND).
2. **Isolação galvânica**: usar drivers como **ADM2483** ou módulos com isolador óptico. Cada nó da rede fica isolado eletricamente do circuito digital.
3. **Aterramento estrela**: padronizar o aterramento da planta.

> **Recomendação prática para alunos:** sempre puxar um fio de GND junto com A e B. É barato, simples e resolve a maioria dos problemas.

---

## 4.9 Conversor USB → RS-485

Análogos aos USB-RS232, mas com chip driver RS-485. Aparecem no SO como COM virtual. Modelos populares:

- **CH340 + MAX485** — clones baratos, funcionam bem para laboratório
- **FT232R + SN75176** — referência profissional
- **CP2102 + MAX3485** — boa relação

A diferença é que, ao transmitir, o conversor precisa **gerenciar automaticamente** o pino DE. Os melhores conversores fazem isso por hardware (auto-direção); outros precisam que o software comute via RTS.

---

## 4.10 Quando NÃO usar RS-485

Apesar de excelente, RS-485 não é a solução para tudo:

- **Taxas muito altas (> 10 Mbps)**: use Ethernet ou EtherCAT.
- **Distâncias > 1200 m**: use fibra óptica ou Ethernet de longo alcance.
- **Múltiplos masters simultâneos**: half-duplex limita a apenas um transmissor por vez. Considere Modbus TCP.
- **Determinismo de tempo real estrito**: RS-485 + Modbus não tem garantia de tempo de resposta. Use Profinet IRT, EtherCAT ou TSN.

---

## 4.11 Tabela Comparativa: RS-232 vs. RS-485

| Característica          | RS-232               | RS-485                  |
|-------------------------|----------------------|--------------------------|
| Sinalização             | Single-ended         | Diferencial              |
| Lógica 1                | −3 a −15 V           | (B − A) > 0,2 V          |
| Lógica 0                | +3 a +15 V           | (B − A) < −0,2 V         |
| Imunidade a ruído       | Baixa                | **Alta**                 |
| Modo comum tolerado     | Nenhum               | **±7 V (até ±60 V)**     |
| Distância (9600 baud)   | 15 m                 | **1200 m**               |
| Taxa máxima             | ~115 kbps prático    | **10 Mbps**              |
| Número de dispositivos  | 1 (ponto-a-ponto)    | **32 (até 256 com chips fracionários)** |
| Duplex                  | Full                 | Half (RS-485) ou Full (RS-422) |
| Fios necessários        | 3 (TX, RX, GND)      | 2 ou 3 (A, B, [GND])     |
| Aplicação típica        | Programação, console | **Redes industriais**    |

---

## 4.12 Roteiro do Laboratório 4.1 — Comunicação RS-485 entre dois PCs

### 4.12.1 Material

- 2 conversores USB → RS-485
- 2 a 5 m de cabo par trançado (UTP cat 5e basta)
- 2 resistores de **120 Ω**
- 2 PCs com terminal serial (PuTTY, RealTerm, ou pyserial)

### 4.12.2 Montagem

```
   PC1 ── USB-485 ─┬─ A ─────────────── A ─┬─ USB-485 ── PC2
                   │                        │
                   │ B ─────────────── B   │
                   │                        │
                  120 Ω                   120 Ω
                   │                        │
                   GND ───────────────── GND
```

### 4.12.3 Procedimento

1. Identifique a porta COM de cada conversor (Gerenciador de Dispositivos no Windows, `dmesg` no Linux).
2. Abra um terminal serial em cada PC, **mesma configuração** (9600 baud, 8N1).
3. Em PC1, digite caracteres e verifique se aparecem em PC2.
4. **Atenção**: RS-485 é half-duplex. Se digitar em ambos simultaneamente, haverá colisão. Estabeleça um turno.

### 4.12.4 Discussão

- Por que é diferente o cabeamento em relação ao Lab RS-232?
- Remova os terminadores. A comunicação ainda funciona? Em qual taxa começa a falhar?
- Acrescente um terceiro PC ao barramento. Funciona? Onde colocar o terminador?

---

## 4.13 Exercícios

### Conceituais

1. Por que sinalização diferencial **rejeita ruído** que sinalização single-ended não rejeita? Use um diagrama vetorial para apoiar sua explicação.
2. Em uma rede RS-485, **quantos terminadores** devem estar presentes? Por quê?
3. Por que o RS-485 é tipicamente **half-duplex** em redes Modbus?

### Análise

4. Em uma rede RS-485 com 12 escravos, faz alguma diferença a **ordem física** dos escravos ao longo do cabo? Comente sobre desempenho elétrico e protocolo Modbus.
5. Calcule a distância máxima de uma rede RS-485 operando em **57600 baud**, baseado na regra heurística "produto taxa × distância ≤ 100 Mbps·m".
6. Você herda uma rede com 25 escravos. Após 23 conectados, o 24º começa a apresentar erros intermitentes. Diagnóstico provável?

### Projeto

7. Desenhe o esquema de uma rede RS-485 conectando **um mestre e 5 escravos**, incluindo:
   - Terminadores (com valor)
   - Resistores de bias (com valores)
   - Aterramento
   - Comprimento e bitola de cabo sugeridos para 100 m
8. **Pesquisa.** Identifique três fabricantes de gateways Modbus RTU ↔ Modbus TCP. Para cada um, anote: modelo, número máximo de escravos suportados, taxa máxima.
9. Em um datasheet de inversor (qualquer marca), identifique:
   - Configuração serial padrão
   - Endereço Modbus default
   - Function codes suportados
10. **Reflexão.** Discuta como a chegada da Ethernet (Modbus TCP) impactou o uso do RS-485 em plantas modernas. Onde RS-485 ainda é a melhor escolha em 2026?

---

## 4.14 Síntese — Para fixar antes do próximo módulo

- **Sinalização diferencial** = imunidade a ruído + distâncias longas.
- **Par trançado** = essencial para que a rejeição de modo comum funcione.
- **120 Ω nas duas extremidades** = sem reflexões.
- **Bias** = nível conhecido quando ninguém transmite.
- **Half-duplex** = um fala, todos escutam; turnos coordenados pela camada superior (Modbus).

---

**Próximo módulo:** [05-introducao-modbus.md](05-introducao-modbus.md)
