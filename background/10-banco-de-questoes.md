# Banco de Questões — Comunicações Industriais e Protocolo Modbus

**Disciplina:** Comunicações Industriais e Protocolo Modbus
**Instituição:** Mekatronik — Advanced Engineering
**Professor:** Prof. Dênis Leite

> Este banco reúne **50 questões** de verificação de aprendizagem, distribuídas pelos temas da disciplina. As questões exigem que o aluno articule o conteúdo teórico dos módulos 1–9 com a experiência prática dos laboratórios 1–11. Questões de cálculo têm dados suficientes para resolução sem consulta externa.

**Legenda de dificuldade:**
- `[B]` Básico — recordar, compreender
- `[I]` Intermediário — aplicar, analisar
- `[A]` Avançado — avaliar, sintetizar, calcular

---

## Bloco 1 — Comunicação Serial Assíncrona (Módulos 2, 3 e 4)

**Q01 `[B]`**
Um frame UART é configurado como 8N1 (8 bits de dados, sem paridade, 1 stop bit).
Desenhe a sequência de bits completa para transmitir o byte `0x41` (letra "A").
Quantos bits são enviados ao todo? Qual é a eficiência de banda — ou seja, que percentual dos bits transmitidos carrega dados úteis?

---

**Q02 `[I]`**
Dois equipamentos trocam dados via UART a 9600 bps com configuração 8E1 (paridade par).
O byte `0xB7` (binário: `1011 0111`) é enviado. Qual deve ser o valor do bit de paridade? O receptor recebe a sequência e calcula paridade ímpar — ele vai aceitar ou rejeitar o frame? Justifique.

---

**Q03 `[I]`**
A 38400 bps com configuração 8N1, calcule:
- a) A duração de um bit.
- b) O tempo de transmissão de um único frame completo.
- c) O tempo necessário para transmitir uma mensagem de 256 bytes (sem pausas entre frames).

---

**Q04 `[B]`**
Explique a diferença entre comunicação simplex, half-duplex e full-duplex.
Para cada modo, dê um exemplo de tecnologia ou protocolo industrial que o utilize.
Em qual modo opera o Modbus RTU? Por quê?

---

**Q05 `[B]`**
O padrão RS-232 define que o nível lógico "1" corresponde a uma tensão **negativa** (tipicamente −12 V), e o nível lógico "0" corresponde a uma tensão **positiva** (+12 V). Essa inversão é chamada de lógica negativa. Por que o RS-232 adota esse esquema em vez da lógica positiva convencional?

---

**Q06 `[I]`**
Um engenheiro precisa interligar dois CLPs com comunicação serial para troca de dados. A distância entre eles é de 25 metros e o ambiente é industrial (motores, inversores de frequência, cabos de alta tensão nas proximidades).
Ele tem disponíveis: conversores USB→RS-232, conversores USB→RS-485 e cabo par trançado blindado.
Qual solução você recomenda? Justifique considerando as especificações elétricas de cada padrão (tensão, distância máxima, imunidade a ruído).

---

**Q07 `[I]`**
Explique o princípio da **sinalização diferencial** usada pelo RS-485.
Por que esse método é mais imune a interferências eletromagnéticas do que a sinalização single-ended do RS-232? Qual é o critério mínimo de tensão diferencial que o receptor RS-485 deve detectar para considerar o sinal válido?

---

**Q08 `[I]`**
Uma rede RS-485 com 8 escravos foi instalada corretamente em daisy-chain. O técnico responsável não instalou os resistores de terminação. A comunicação funciona aparentemente bem a baixas velocidades (9600 bps), mas apresenta erros frequentes a 115200 bps. Explique o fenômeno físico que causa esse comportamento e como corrigi-lo.

---

**Q09 `[A]`**
Uma planta industrial tem 20 medidores de energia distribuídos em uma área de 800 metros de extensão, todos com interface RS-485 Modbus RTU. Um técnico propõe conectar todos em uma única rede RS-485 a 9600 bps. Outro propõe dividir em dois segmentos RS-485 independentes com um gateway.
Avalie ambas as propostas considerando: número máximo de unidades de carga em RS-485, distância, terminação, latência de polling e facilidade de manutenção. Qual você escolheria?

---

**Q10 `[B]`**
Quais são as duas diferenças fundamentais entre o padrão RS-232 e o RS-485 em relação a:
- a) número de dispositivos na mesma linha;
- b) distância máxima de cabo;
- c) nível de tensão dos sinais;
- d) topologia de conexão.

---

## Bloco 2 — Protocolo Modbus: Fundamentos e RTU (Módulos 5 e 6)

**Q11 `[B]`**
O Modbus define quatro categorias de dados em seu modelo de dados. Preencha a tabela abaixo:

| Categoria | Tipo de dado | Acesso | Function Code de leitura |
|-----------|-------------|--------|--------------------------|
| Coils | | | |
| Discrete Inputs | | | |
| Holding Registers | | | |
| Input Registers | | | |

Para cada categoria, dê um exemplo concreto de variável industrial que ela poderia representar.

---

**Q12 `[I]`**
Um escravo Modbus recebe uma requisição FC03 válida, mas o endereço solicitado está fora do mapa de registradores disponíveis. Qual resposta o escravo deve enviar? Descreva os campos dessa resposta de exceção, incluindo como o Function Code é modificado na resposta.

---

**Q13 `[A]`**
Monte o frame Modbus RTU completo (em hexadecimal) para a seguinte requisição:
- Slave Address: 7
- Função: Ler 6 Input Registers
- Endereço inicial: 0 (registrador 0x0000)
- Quantidade: 6

Mostre todos os campos do frame. O CRC-16 calculado para os bytes `[07 04 00 00 00 06]` é `0xC1FA` (LSB = `0xFA`, MSB = `0xC1`). Qual é o frame completo com o CRC na ordem de transmissão correta?

---

**Q14 `[I]`**
Em Modbus RTU, o início e o fim de um frame são detectados por **silêncio no barramento** (t3.5). Isso cria uma dependência importante: todos os dispositivos na rede devem estar configurados com o mesmo baud rate.
Por que um frame Modbus RTU não tem campos de "início de mensagem" ou "comprimento" explícitos, como o Modbus ASCII tem com `:` e `CRLF`?

---

**Q15 `[A]`**
A 9600 bps com frame 8N1, calcule o valor do intervalo de silêncio t3.5 em milissegundos (use 11 bits por caractere).
Em seguida, explique o que acontece em duas situações distintas:
- a) O escravo começa a responder em 2 ms (antes do t3.5 acabar).
- b) O mestre aguarda apenas 2 ms pela resposta antes de considerar timeout.

---

**Q16 `[I]`**
Compare Modbus RTU e Modbus ASCII:

| Critério | Modbus RTU | Modbus ASCII |
|----------|-----------|-------------|
| Delimitador de frame | | |
| Verificação de integridade | | |
| Eficiência de banda | | |
| Legibilidade por humanos | | |
| Caso de uso típico | | |

Em que cenário específico o Modbus ASCII seria preferível ao RTU, apesar de sua menor eficiência?

---

**Q17 `[I]`**
Um mestre Modbus RTU envia uma requisição FC16 (Write Multiple Registers) para escrever 2 registradores no escravo 5, começando no endereço 106. Os valores a escrever são: Registrador 106 = `0x4382`, Registrador 107 = `0x0000`.
- a) O que representa o valor `0x43820000` em IEEE 754 FLOAT32?
- b) Quantos bytes de dados o frame de requisição contém no campo PDU (excluindo Slave Address e CRC)?

---

**Q18 `[I]`**
Um mestre Modbus RTU lê o escravo 3 e recebe a seguinte resposta (em hex):
`03 84 02`

Decodifique completamente essa resposta campo a campo. O que ela significa? Que ação o mestre deve tomar?

---

**Q19 `[I]`**
O CRC-16 do Modbus RTU é transmitido em ordem **little-endian** (LSB primeiro), ao contrário dos demais campos do frame que são big-endian. Explique por que esse detalhe frequentemente causa bugs em implementações manuais e descreva como verificar se uma implementação está tratando o CRC corretamente ao analisar um frame no Wireshark ou analisador serial.

---

**Q20 `[A]`**
Uma planta tem 10 medidores RS-485 Modbus RTU. O SCADA precisa ler 8 Input Registers de cada medidor a cada ciclo. A rede opera a 9600 bps com frames 8N1. Considere:
- Tempo de transmissão de 1 byte a 9600 bps com 11 bits/char ≈ 1,146 ms
- Frame de requisição FC04 (8 regs): 8 bytes
- Frame de resposta FC04 (8 regs): 21 bytes (1+1+1+16+2)
- Tempo de processamento do escravo: 5 ms
- Intervalo entre frames (t3.5): 4 ms

Calcule o tempo total para um ciclo completo de polling dos 10 medidores. O SCADA consegue atualizar todos em menos de 1 segundo?

---

## Bloco 3 — TCP/IP e Modbus TCP (Módulos 8 e 9)

**Q21 `[B]`**
Explique a diferença entre TCP e UDP quanto a:
- a) Orientação a conexão
- b) Garantia de entrega
- c) Controle de fluxo e congestionamento

Por que o Modbus TCP usa TCP e não UDP? Há algum caso onde UDP seria uma escolha válida para telemetria industrial?

---

**Q22 `[B]`**
O que é um socket? Descreva os quatro elementos que identificam unicamente uma conexão TCP entre dois dispositivos (a chamada "4-tupla"). Quando dois clientes Modbus TCP diferentes se conectam ao mesmo servidor simultaneamente, como o sistema operacional diferencia as duas conexões?

---

**Q23 `[I]`**
O simulador ModbusDeviceSIM usa a porta **5020** em vez da porta padrão Modbus TCP **502**.
- a) Por que a porta 502 pode falhar em sistemas Android?
- b) A porta 5020 é uma porta "registrada" ou "efêmera"? Qual a faixa de cada categoria?
- c) O que precisa ser modificado no EasyModbusTCP, no Python/pymodbus e no Node-RED para se conectar ao simulador?

---

**Q24 `[B]`**
Descreva os campos do cabeçalho MBAP (Modbus Application Protocol Header) e a função de cada um:

| Campo | Tamanho | Função |
|-------|---------|--------|
| Transaction Identifier | | |
| Protocol Identifier | | |
| Length | | |
| Unit Identifier | | |

Por que o Protocol Identifier tem valor fixo igual a 0?

---

**Q25 `[I]`**
O frame Modbus TCP capturado no Wireshark mostra (em hex):
`00 0F 00 00 00 06 01 04 00 00 00 02`

Decodifique **campo a campo** todo o frame, identificando: qual dispositivo é alvo, qual função é requisitada, quais registradores serão lidos, e qual é o Transaction ID desta transação.

---

**Q26 `[I]`**
O Modbus RTU usa CRC-16 para detecção de erros. O Modbus TCP não tem CRC. Isso significa que o Modbus TCP não tem proteção contra erros de transmissão?
Explique qual mecanismo da pilha TCP/IP garante a integridade dos dados e em qual camada ele opera.

---

**Q27 `[I]`**
O campo **Unit Identifier** no MBAP do Modbus TCP tem valor 1 em todas as práticas com o ModbusDeviceSIM. Em qual cenário esse campo teria um valor diferente de 1 e seria essencial para o funcionamento correto do sistema? Descreva a arquitetura desse cenário.

---

**Q28 `[I]`**
Um servidor Modbus TCP pode aceitar múltiplas conexões simultâneas de diferentes clientes. O campo **Transaction Identifier** existe justamente para suportar um padrão avançado de uso. Descreva esse padrão (pipeline de requisições) e explique como o Transaction Identifier permite que o cliente correlacione respostas com requisições quando múltiplas requisições estão em voo ao mesmo tempo.

---

**Q29 `[A]`**
Compare as latências típicas de uma leitura simples em dois cenários:

**Cenário A:** Modbus RTU a 9600 bps, frame de requisição 8 bytes, frame de resposta 21 bytes, t3.5 = 4 ms, processamento do escravo = 5 ms.

**Cenário B:** Modbus TCP em Ethernet 100 Mbps, RTT médio na LAN = 1 ms, processamento do servidor = 1 ms.

Calcule a latência total de ida e volta (do envio da requisição ao recebimento da resposta completa) em cada cenário. Em que tipo de aplicação industrial a diferença de latência seria crítica?

---

**Q30 `[A]`**
Um gateway Modbus RTU-to-TCP é instalado em uma fábrica. Clientes TCP (SCADA em nuvem) enviam requisições para 8 escravos RTU diferentes, todos no mesmo barramento RS-485 com IDs 1 a 8.
- a) Como o gateway identifica para qual escravo RS-485 encaminhar cada requisição TCP recebida?
- b) Por que o gateway não pode processar duas requisições para escravos diferentes em paralelo, mesmo tendo uma conexão TCP de alta velocidade?
- c) O que acontece com a latência observada pelo cliente TCP quando o gateway precisar serializar as requisições?

---

## Bloco 4 — Ferramentas e Prática com os Simuladores (Labs 1–6)

**Q31 `[B]`**
No MK-EM3P e no MK-VFD7, existe uma distinção importante: medições são lidas com **FC04** e configurações são lidas/escritas com **FC03**.
- a) Por que essa distinção existe no Modbus? O que impede tecnicamente um cliente de usar FC03 para ler um Input Register?
- b) No EasyModbusTCP, que campo você configura para selecionar entre FC03 e FC04?
- c) Se você usar FC03 para tentar ler o endereço 0 do MK-EM3P (que é um Input Register), o que acontece?

---

**Q32 `[A]`**
O MK-EM3P retorna a tensão de fase L1-N como dois registradores consecutivos em FLOAT32 big-endian (word order ABCD):
- Registrador 0: `0x4360`
- Registrador 1: `0x0000`

Decodifique manualmente o valor da tensão:
- a) Monte o valor de 32 bits concatenando os dois registradores na ordem ABCD.
- b) Identifique o bit de sinal, o campo do expoente e a mantissa.
- c) Calcule o valor decimal. A tensão faz sentido para uma rede elétrica trifásica 380/220 V?

---

**Q33 `[I]`**
Escreva o código Python (pymodbus 3.x) completo e funcional para:
1. Conectar ao MK-EM3P no IP `192.168.1.100`, porta `5020`, Unit ID `1`.
2. Ler os registradores 0 e 1 (tensão L1-N).
3. Converter os dois registradores em um valor FLOAT32 (word order ABCD).
4. Exibir o resultado formatado.
5. Fechar a conexão.

Use `struct.unpack` para a decodificação do float.

---

**Q34 `[I]`**
No Python com pymodbus 3.x, qual é a diferença prática entre `read_input_registers()` e `read_holding_registers()`?
Em termos de Modbus, a qual Function Code cada método corresponde?
O que acontece se você chamar `read_holding_registers(address=0, count=2, slave=1)` em um dispositivo que tem o endereço 0 como Input Register (não como Holding Register)?

---

**Q35 `[I]`**
Você está implementando um logger em Python que coleta dados do MK-EM3P a cada 5 segundos e salva em CSV. Após 20 minutos de execução, o script trava silenciosamente sem erros visíveis. Identifique três causas prováveis desse comportamento e descreva como adicionar tratamento de erros para evitá-las.

---

**Q36 `[I]`**
No MK-VFD7, o Control Word está no Holding Register 100. Os valores possíveis são:
- `0`: STOP
- `1`: RUN FORWARD
- `3`: RUN REVERSE

A frequência de referência está no Holding Register 101 (UINT16, valor direto em décimos de Hz — ex: `500` = 50,0 Hz).

Escreva o código Python para:
1. Configurar frequência de referência para 45,0 Hz.
2. Dar START no VFD em modo FORWARD.
3. Aguardar 3 segundos.
4. Dar STOP.

---

**Q37 `[I]`**
No Node-RED, você configura um nó `modbus-read` com os seguintes parâmetros:
- FC: `4` (Read Input Registers)
- Address: `0`
- Quantity: `4`
- Server: IP do smartphone, porta 5020

O nó `modbus-read` entrega os dados brutos como um array de inteiros de 16 bits. Escreva o código de um nó `function` subsequente que:
1. Extraia os dois primeiros inteiros (registradores 0 e 1).
2. Converta para FLOAT32 big-endian (ABCD) em JavaScript.
3. Passe o valor convertido como `msg.payload` para o próximo nó.

---

**Q38 `[I]`**
Um aluno tenta ler o MK-EM3P com EasyModbusTCP e recebe resposta, mas os valores de tensão parecem ser números absurdos (ex: `1.4e-38` ou `3.4e+38`). A conexão está funcionando e os registradores estão sendo lidos com sucesso.
Qual é a causa mais provável? Como corrigir?

---

**Q39 `[B]`**
Liste os passos de diagnóstico, em ordem lógica de execução, quando o EasyModbusTCP retorna "Connection refused" ao tentar conectar ao ModbusDeviceSIM rodando no smartphone.
Inclua pelo menos 5 passos distintos, do mais básico ao mais específico.

---

**Q40 `[A]`**
Compare as três abordagens de implementação de cliente Modbus TCP praticadas nos labs:

| Critério | EasyModbusTCP | Python + pymodbus | Node-RED |
|----------|--------------|------------------|---------|
| Curva de aprendizado | | | |
| Flexibilidade de lógica | | | |
| Dashboard em tempo real | | | |
| Registro histórico (CSV/DB) | | | |
| Integração com outros sistemas | | | |
| Caso de uso ideal | | | |

Em qual das três você implementaria um sistema de monitoramento de 10 inversores com alarmes por e-mail e histórico de 30 dias? Justifique.

---

## Bloco 5 — Integração Multi-Dispositivos (Labs G1–G4)

**Q41 `[I]`**
Na Prática Grupo 1, três clientes Modbus TCP se conectam simultaneamente ao mesmo VFD simulado. Dois clientes tentam escrever no Control Word (HR 100) ao mesmo tempo — um enviando STOP (`0`) e outro enviando RUN (`1`).
- a) O que o servidor Modbus TCP faz com as duas requisições simultâneas?
- b) Qual valor estará no registrador após as duas escritas? É determinístico?
- c) Como sistemas industriais reais resolvem o problema de acesso concorrente de escrita?

---

**Q42 `[I]`**
Na Prática Grupo 2, um único cliente Python controla 3 VFDs diferentes usando a classe `MultiVfd`. O design cria **três instâncias separadas de `ModbusTcpClient`**, uma por VFD.
Por que não usar uma única conexão TCP e variar o Unit Identifier para acessar cada VFD?
Descreva o cenário onde usar um único cliente com Unit IDs diferentes seria a abordagem correta.

---

**Q43 `[A]`**
Na Prática Grupo 2, implemente em pseudocódigo a lógica de **partida sequencial com verificação de estado**:
1. Conectar aos 3 VFDs (IPs distintos, mesma porta).
2. Para cada VFD (em sequência), definir frequência de 30 Hz e dar START.
3. Aguardar 2 segundos entre cada partida (staggered start).
4. Após todos rodando, aumentar gradualmente para 50 Hz (incrementos de 5 Hz a cada 3 s).
5. Se qualquer VFD falhar ao responder em 2 tentativas, registrar o erro e continuar com os demais.

---

**Q44 `[I]`**
Na Prática Grupo 3, cada aluno opera seu próprio VFD mas todos os três clientes também podem **ler** os dados dos VFDs dos outros colegas.
Um aluno relata que os dados de tensão que ele lê do VFD do colega aparecem com valores deslocados — sempre mostra o valor correto de frequência em vez de tensão.
Identifique a causa mais provável e corrija o código.

---

**Q45 `[A]`**
Na Prática Grupo 4 (mini-planta), o sistema deve implementar um **interlock elétrico**: se o MK-EM3P reportar demanda de potência acima de 85% da capacidade contratada, ambos os VFDs devem ser parados automaticamente.

Escreva a lógica completa em Python (usando pymodbus), incluindo:
- Leitura periódica da demanda do medidor (considere que está no Input Register 20, FLOAT32).
- Comparação com threshold de 85 kW.
- Envio de STOP para ambos os VFDs se o threshold for ultrapassado.
- Log de cada evento de interlock com timestamp.

---

**Q46 `[I]`**
O Modbus TCP não possui mecanismos nativos de **autenticação** ou **criptografia**. Um dispositivo Modbus TCP exposto em uma rede corporativa pode ser acessado por qualquer host que tenha conectividade IP.
- a) Cite dois vetores de ataque que esse modelo representa em uma planta industrial.
- b) Liste três mitigações práticas que podem ser adotadas sem substituir o protocolo Modbus.
- c) Existe alguma extensão ou encapsulamento do Modbus que adiciona segurança? Mencione brevemente.

---

**Q47 `[A]`**
Você precisa dimensionar uma solução Modbus TCP para monitorar **50 inversores de frequência** em uma planta, cada um com 20 registradores de interesse. O requisito é atualizar todos os valores em no máximo **5 segundos**.

Assuma: RTT médio na LAN = 2 ms por requisição, processamento do servidor = 2 ms, tempo de parsing no cliente = 0 ms.

- a) Calcule o tempo mínimo para um polling sequencial dos 50 inversores (uma requisição por vez).
- b) O requisito de 5 segundos é atendido com polling sequencial?
- c) Proponha uma estratégia de paralelismo (múltiplos threads ou clientes) para cumprir o requisito e calcule quantos threads seriam necessários.

---

**Q48 `[B]`**
Você migrou todo o código Python desenvolvido nos labs do ModbusDeviceSIM (porta 5020, Unit ID 1) para um ambiente real com um medidor comercial (porta 502, Unit ID 1).
Liste **todos** os pontos de configuração que precisam ser verificados ou alterados:
- No código Python.
- No Node-RED.
- No EasyModbusTCP.
- Na rede (firewall, roteador).

---

**Q49 `[A]`**
Compare as duas arquiteturas abaixo para integrar 8 medidores de energia RS-485 com um SCADA em nuvem:

**Arquitetura A:** SCADA → Modbus TCP → Gateway RTU-TCP → barramento RS-485 (8 medidores)

**Arquitetura B:** SCADA → MQTT (broker em nuvem) ← Node-RED (local) → Modbus TCP/RTU → 8 medidores

Avalie cada arquitetura considerando: latência, confiabilidade em falha de internet, volume de dados, complexidade de implementação, e custo. Qual você escolheria para uma planta em área remota com link de internet instável?

---

**Q50 `[A]`**
**Questão integradora:** Você é o engenheiro responsável pela integração digital de uma planta com os seguintes equipamentos já instalados:
- 6 inversores de frequência com interface **Modbus RTU RS-485** (IDs 1–6 no mesmo barramento)
- 2 medidores de energia com interface **Modbus RTU RS-485** (IDs 7–8, mesmo barramento)
- 1 controlador de temperatura com interface **Modbus TCP** (IP fixo na rede local)

Requisitos:
- Dashboard em tempo real visível via browser
- Histórico de 90 dias em banco de dados local
- Alarme por e-mail quando qualquer inversor ultrapassar 90% da frequência máxima
- Operadores devem poder alterar frequência de referência dos inversores via dashboard
- O sistema deve continuar monitorando mesmo em caso de falha de um único dispositivo

Elabore a **arquitetura completa** da solução, descrevendo:
1. Hardware necessário (gateway, servidor, etc.)
2. Software e ferramentas (Node-RED, Python, banco de dados, etc.)
3. Topologia de rede
4. Estratégia de polling e atualização
5. Tratamento de falhas individuais de dispositivo
6. Estrutura do dashboard (quais visualizações)

Não há uma única resposta correta — a avaliação é baseada na coerência técnica e na justificativa das escolhas.

---

## Referência Cruzada por Módulo

| Questões | Módulo / Lab |
|----------|-------------|
| Q01–Q05 | Módulo 2 — Comunicação Serial Assíncrona |
| Q06–Q10 | Módulos 3 e 4 — RS-232 e RS-485 |
| Q11–Q15 | Módulo 5 e 6 — Introdução ao Modbus e Modbus RTU |
| Q16–Q20 | Módulo 6 — Modbus RTU (avançado) |
| Q21–Q25 | Módulos 8 e 9 — TCP/IP e Modbus TCP |
| Q26–Q30 | Módulo 9 — Modbus TCP (avançado) |
| Q31–Q35 | Labs 1–3 — EM3P com EasyModbus e Python |
| Q36–Q40 | Labs 4–6 — VFD7 com Python e Node-RED |
| Q41–Q45 | Labs G1–G4 — Práticas em grupo |
| Q46–Q50 | Síntese — Integração e projeto de sistemas |

---

**Prof. Dênis Leite**
Mekatronik — Advanced Engineering
*Versão: 2026.1*
