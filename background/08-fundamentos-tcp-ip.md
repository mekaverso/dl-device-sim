# Módulo 8 — Fundamentos de Redes TCP/IP

> *"Antes de falar Modbus TCP, é preciso entender o TCP."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Posicionar protocolos em modelo em camadas (OSI e TCP/IP).
2. Compreender endereçamento IPv4, máscaras de subrede e gateway padrão.
3. Diferenciar **TCP** (orientado a conexão) de **UDP** (sem conexão).
4. Explicar o **three-way handshake** do TCP.
5. Usar comandos básicos de diagnóstico (`ping`, `ipconfig`, `arp`, `netstat`, `tracert`).
6. Entender o conceito de **sockets** e **portas**.

---

## 8.1 Por Que Precisamos de Modelos em Camadas?

Imagine que você quer enviar uma carta para um colega em outro país:

```
   1. Você escreve o conteúdo                       (semântica)
   2. Coloca em um envelope                          (formato)
   3. Endereça com nome e endereço                   (endereçamento)
   4. Cola um selo                                   (custo/garantia)
   5. Deposita no correio                            (entrega)
   6. Correio nacional encaminha                     (roteamento)
   7. Avião transporta                               (transporte)
   8. Correio do destino entrega                     (entrega final)
```

Cada **camada** tem uma responsabilidade isolada. Você não precisa saber em qual avião sua carta voou — você confia no correio. O correio, por sua vez, não lê o conteúdo da carta — apenas se preocupa em entregá-la.

**Em redes de computadores funciona igual.** Várias camadas independentes cooperam. Foi assim que a Internet conseguiu evoluir: pode-se substituir uma camada sem afetar as outras.

---

## 8.2 Modelo OSI (7 Camadas)

O modelo de referência **OSI** (Open Systems Interconnection), publicado pela ISO em 1984, é teórico mas serve para discussão:

| # | Camada               | Função                                                  | Exemplos                  |
|---|----------------------|---------------------------------------------------------|---------------------------|
| 7 | Aplicação            | Lógica de aplicação                                     | HTTP, FTP, **Modbus**     |
| 6 | Apresentação         | Codificação, criptografia                              | TLS, ASCII, JPEG          |
| 5 | Sessão               | Gerenciamento de sessão                                | (raro em TCP/IP moderno)  |
| 4 | Transporte           | Confiabilidade fim-a-fim                                | **TCP**, UDP              |
| 3 | Rede                 | Endereçamento global e roteamento                      | **IP** (v4, v6)           |
| 2 | Enlace               | Endereçamento físico, controle de acesso ao meio       | Ethernet (MAC), Wi-Fi     |
| 1 | Física               | Sinais elétricos, óticos, eletromagnéticos             | Cabos, conectores, rádio  |

---

## 8.3 Modelo TCP/IP (4 Camadas — o "real")

O modelo TCP/IP é mais pragmático e refletido na implementação real:

| Camada            | Função                                  | Protocolos típicos                  |
|-------------------|------------------------------------------|-------------------------------------|
| Aplicação         | Aplicações finais                       | HTTP, DNS, SMTP, **Modbus TCP**, MQTT |
| Transporte        | Confiabilidade fim-a-fim                | **TCP**, UDP                        |
| Rede (Internet)   | Roteamento entre redes                  | **IP**, ICMP, ARP                   |
| Enlace + Física   | Acesso ao meio físico                   | Ethernet, Wi-Fi, PPP                |

### Mapeamento OSI → TCP/IP

```
   OSI                               TCP/IP
   ┌─────────────────┐              ┌─────────────────┐
   │ 7. Aplicação    │              │                 │
   ├─────────────────┤              │   Aplicação     │
   │ 6. Apresentação │   ──fundem──►│                 │
   ├─────────────────┤              │                 │
   │ 5. Sessão       │              │                 │
   ├─────────────────┤              ├─────────────────┤
   │ 4. Transporte   │              │   Transporte    │
   ├─────────────────┤              ├─────────────────┤
   │ 3. Rede         │              │   Rede          │
   ├─────────────────┤              ├─────────────────┤
   │ 2. Enlace       │              │                 │
   ├─────────────────┤   ──fundem──►│   Enlace/Física │
   │ 1. Física       │              │                 │
   └─────────────────┘              └─────────────────┘
```

> **Em qual camada vive o Modbus TCP?** Camada de **aplicação**. Ele utiliza TCP (transporte) e IP (rede) abaixo. Não se preocupe com ARP, MAC, Ethernet — o sistema operacional cuida disso.

---

## 8.4 Endereçamento IPv4

### 8.4.1 O endereço IP

Um endereço IPv4 tem **32 bits**, escrito como **4 octetos** decimais separados por pontos:

```
   192.168.1.45
   ↑   ↑   ↑ ↑
   │   │   │ └── 45  = 00101101
   │   │   └──── 1   = 00000001
   │   └──────── 168 = 10101000
   └──────────── 192 = 11000000

   Binário: 11000000.10101000.00000001.00101101
```

Existem **2^32 ≈ 4,3 bilhões** de endereços possíveis. Aparentemente muito; na prática, **insuficiente** — e por isso existe NAT, IPv6, etc.

### 8.4.2 Faixas privadas (RFC 1918)

Há três faixas reservadas para **uso interno** (não roteáveis na Internet pública):

| Faixa                  | Notação CIDR     | Tamanho     |
|------------------------|------------------|-------------|
| 10.0.0.0 – 10.255.255.255   | 10.0.0.0/8       | 16.777.214  |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12    | 1.048.574   |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | 65.534      |

**A maioria das redes domésticas e industriais usam 192.168.x.x** ou **10.x.x.x**.

### 8.4.3 Endereços especiais

| Endereço         | Significado                                |
|------------------|--------------------------------------------|
| 127.0.0.1        | Loopback — refere a si mesmo               |
| 0.0.0.0          | "Qualquer endereço" / endereço não atribuído |
| 255.255.255.255  | Broadcast geral                            |
| 169.254.x.x      | APIPA — autoconfiguração na ausência de DHCP |

### 8.4.4 Máscara de subrede

A **máscara** divide o endereço IP em duas partes:

- **Parte de rede:** identifica a sub-rede
- **Parte de host:** identifica o equipamento dentro da sub-rede

```
   IP:        192.168.1.45
   Máscara:   255.255.255.0   (ou /24 em notação CIDR)

   Rede:      192.168.1.0     ← bits onde a máscara é 1
   Host:      .45             ← bits onde a máscara é 0
```

**Notação CIDR** usa um número que indica **quantos bits são da rede**:

| Máscara             | CIDR  | Hosts úteis |
|---------------------|-------|-------------|
| 255.0.0.0           | /8    | 16.777.214  |
| 255.255.0.0         | /16   | 65.534      |
| 255.255.255.0       | /24   | 254         |
| 255.255.255.128     | /25   | 126         |
| 255.255.255.252     | /30   | 2           |

> **Regra prática:** duas máquinas estão na **mesma sub-rede** se, ao aplicar a máscara, o **mesmo número de rede** resultar.

**Exemplo:**

- IP1 = 192.168.1.45, máscara /24 → rede = 192.168.1.0
- IP2 = 192.168.1.200, máscara /24 → rede = 192.168.1.0 → **mesma rede** ✓
- IP3 = 192.168.2.45, máscara /24 → rede = 192.168.2.0 → **rede diferente** ✗

### 8.4.5 Gateway padrão

O **gateway** é o endereço para onde enviar pacotes destinados a **outras redes**. Tipicamente é o roteador da rede.

```
   PC (192.168.1.45) quer falar com 8.8.8.8 (Google DNS)
                      │
                      ▼
   "Não é da minha rede 192.168.1.0/24..."
                      │
                      ▼
   "Manda pro gateway 192.168.1.1"
                      │
                      ▼
   O roteador 192.168.1.1 encaminha à Internet
```

---

## 8.5 ARP — Mapear IP em MAC

Endereços IP são **lógicos**. Para entregar fisicamente um pacote em uma rede Ethernet, precisa-se do **endereço MAC** (48 bits, identificador do hardware de rede).

O **ARP** (*Address Resolution Protocol*) traduz IP → MAC:

```
   PC quer falar com 192.168.1.200, mas só sabe o IP.

   PC envia broadcast Ethernet: "Quem tem o IP 192.168.1.200?"
   Equipamento responde: "Sou eu, meu MAC é AA:BB:CC:11:22:33."
   PC armazena o mapeamento em sua tabela ARP.
```

Para ver a tabela ARP no Windows:
```
   arp -a
```

---

## 8.6 TCP vs. UDP

Sobre o IP, há dois protocolos de transporte principais:

### 8.6.1 TCP (Transmission Control Protocol)

- **Orientado a conexão**: estabelece sessão antes de transmitir.
- **Confiável**: garante entrega, ordem, sem duplicação.
- **Controle de fluxo**: ajusta velocidade conforme o receptor.
- **Mais overhead**: cabeçalho de 20+ bytes, ACKs, retransmissão.

### 8.6.2 UDP (User Datagram Protocol)

- **Sem conexão**: cada pacote é independente.
- **Não-confiável**: pacotes podem ser perdidos, duplicados, fora de ordem.
- **Mais leve**: cabeçalho de apenas 8 bytes.
- **Mais rápido**: ideal para streaming, jogos, VoIP, DNS.

### 8.6.3 Comparação

| Aspecto                | TCP                   | UDP                |
|------------------------|-----------------------|--------------------|
| Conexão                | Sim                   | Não                |
| Confiabilidade         | Garantida             | Não garantida      |
| Ordem                  | Garantida             | Não garantida      |
| Controle de fluxo      | Sim                   | Não                |
| Latência               | Maior                 | Menor              |
| Cabeçalho              | 20+ bytes             | 8 bytes            |
| Uso típico             | HTTP, **Modbus TCP**, SSH, e-mail | DNS, streaming, jogos |

> **Modbus TCP usa TCP** (e não UDP). Por quê? Porque a integridade é mandatória em controle industrial — não se pode tolerar um pacote perdido sem retransmissão.

---

## 8.7 O Three-Way Handshake do TCP

Antes de qualquer dado, TCP estabelece a conexão em três passos:

```
   Cliente                              Servidor
      │                                     │
      │  ──── SYN, seq=X      ──────►       │
      │                                     │
      │  ◄──── SYN+ACK, ack=X+1, seq=Y ──── │
      │                                     │
      │  ──── ACK, ack=Y+1     ──────►      │
      │                                     │
      │  ════════ Conexão estabelecida ════ │
      │                                     │
      │  ──── DADOS              ───►       │
      │  ◄──── DADOS                ────    │
      │  ... etc ...                        │
      │                                     │
      │  ──── FIN                  ───►     │
      │  ◄──── FIN+ACK             ────     │
      │  ──── ACK                  ───►     │
      │                                     │
      │  ════════ Conexão encerrada ═══════ │
```

**Implicação prática:** abrir uma conexão TCP custa **uma volta de rede** (latência ~ms). Por isso, em Modbus TCP, **mantém-se a conexão aberta** entre transações.

---

## 8.8 Sockets e Portas

### 8.8.1 O que é uma porta?

Uma **porta** é um número de 16 bits (0–65535) que **multiplexa** múltiplas aplicações no mesmo IP:

```
   ┌─────────────────────┐
   │     PC 192.168.1.5  │
   │                     │
   │  porta 80   ◄────── Web server
   │  porta 22   ◄────── SSH server
   │  porta 502  ◄────── Modbus TCP server
   │  porta 5432 ◄────── PostgreSQL
   └─────────────────────┘
```

Quando um pacote chega ao IP do PC, o sistema operacional olha a porta de destino para decidir **qual aplicação** vai receber.

### 8.8.2 Portas bem conhecidas

| Porta | Protocolo | Aplicação              |
|-------|-----------|------------------------|
| 20-21 | TCP       | FTP                    |
| 22    | TCP       | SSH                    |
| 23    | TCP       | Telnet                 |
| 25    | TCP       | SMTP (e-mail)          |
| 53    | TCP/UDP   | DNS                    |
| 80    | TCP       | HTTP                   |
| 443   | TCP       | HTTPS                  |
| 502   | TCP       | **Modbus TCP**         |
| 802   | TCP       | Modbus TCP Secure (TLS)|
| 1883  | TCP       | MQTT (não criptografado)|
| 8883  | TCP       | MQTT/TLS               |
| 4840  | TCP       | OPC UA                 |

> **Portas privilegiadas** (0–1023) historicamente exigiam permissão de administrador (root) para que processos pudessem se "ligar" a elas. Em Android moderno, **algumas firmwares OEM ainda restringem** a porta 502, motivo pelo qual o **ModbusDeviceSIM agora usa a porta 5020** nas práticas.

### 8.8.3 O conceito de socket

Um **socket** é a abstração de programação que representa uma extremidade de comunicação. É identificado por **(IP, porta, protocolo)**.

Em código Python:

```python
import socket

# Cria socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Cliente: conecta a um servidor remoto
sock.connect(("192.168.1.45", 5020))

# Envia bytes
sock.send(b"\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02")

# Recebe resposta
response = sock.recv(1024)
print(response)

sock.close()
```

---

## 8.9 Comandos Essenciais de Diagnóstico

### 8.9.1 ipconfig (Windows) / ifconfig ou ip a (Linux)

Mostra a configuração de rede do PC.

```
   C:\> ipconfig

   Ethernet adapter Wi-Fi:
       IPv4 Address. . . . . . : 192.168.1.45
       Subnet Mask . . . . . . : 255.255.255.0
       Default Gateway . . . . : 192.168.1.1
```

### 8.9.2 ping

Envia pacotes ICMP. Testa **alcançabilidade** e **latência**.

```
   C:\> ping 192.168.1.45

   Pinging 192.168.1.45 with 32 bytes of data:
   Reply from 192.168.1.45: bytes=32 time=2ms TTL=64
   ...
```

> **Importante:** alguns equipamentos **não respondem a ping** por configuração (firewall, ICMP desabilitado). O dispositivo pode estar funcionando perfeitamente em Modbus TCP mesmo sem responder ao ping.

### 8.9.3 tracert (Windows) / traceroute (Linux)

Mostra o caminho que um pacote percorre.

```
   C:\> tracert 8.8.8.8

   Tracing route to dns.google [8.8.8.8]:
     1     1 ms     1 ms     1 ms  192.168.1.1
     2    10 ms     8 ms     9 ms  100.64.0.1
     3    15 ms    14 ms    16 ms  isp-router.example.com
   ...
```

### 8.9.4 netstat

Lista conexões TCP/UDP ativas e sockets em escuta.

```
   C:\> netstat -an | findstr 5020

   TCP    0.0.0.0:5020       0.0.0.0:0       LISTENING
   TCP    192.168.1.45:5020  192.168.1.20:54123  ESTABLISHED
```

### 8.9.5 arp -a

Lista a tabela ARP atual.

```
   C:\> arp -a

   Interface: 192.168.1.45 --- 0xb
     Internet Address      Physical Address      Type
     192.168.1.1           aa-bb-cc-dd-ee-ff     dynamic
     192.168.1.200         11-22-33-44-55-66     dynamic
```

### 8.9.6 nslookup

Resolve nomes DNS.

```
   C:\> nslookup modbus.org

   Server:  192.168.1.1
   Address: 192.168.1.1
   Name:    modbus.org
   Address: 104.21.85.142
```

---

## 8.10 Encapsulamento — Como Um Pacote Modbus TCP "Embarca"

Quando você envia um frame Modbus TCP, ele é **embrulhado** sucessivamente em cabeçalhos:

```
   ┌─────────────────────────────────────────────────────────┐
   │ Ethernet Header (14 bytes)                              │
   │  ┌─────────────────────────────────────────────────────┐│
   │  │ IP Header (20 bytes)                                ││
   │  │  ┌─────────────────────────────────────────────────┐││
   │  │  │ TCP Header (20+ bytes)                          │││
   │  │  │  ┌─────────────────────────────────────────────┐│││
   │  │  │  │ MBAP Header (7 bytes) + Modbus PDU (≤ 253)  ││││
   │  │  │  └─────────────────────────────────────────────┘│││
   │  │  └─────────────────────────────────────────────────┘││
   │  └─────────────────────────────────────────────────────┘│
   └─────────────────────────────────────────────────────────┘
```

Para um frame Modbus TCP pequeno (ex.: leitura de 2 registradores), o overhead total no fio é:

- Ethernet: 14 + 4 (CRC) = 18 bytes
- IP: 20 bytes
- TCP: 20 bytes
- Modbus MBAP + PDU: 12 bytes (típico)

**Total: 70 bytes** para transmitir 4 bytes de dado útil. Eficiência: ~6 %.

> Em Modbus RTU, esse mesmo frame teria 8 bytes. Modbus TCP é "ineficiente" em pequenas transações, mas **a rede Ethernet** é tão rápida (10 Mbps+ em qualquer rede moderna) que isso não importa na prática.

---

## 8.11 Wireshark — A Janela para a Rede

**Wireshark** é o analisador de tráfego padrão da indústria. Captura todos os pacotes que passam por uma interface de rede e os exibe decodificados.

### 8.11.1 Por que usar Wireshark em Modbus?

- **Ver os bytes reais** transmitidos
- **Diagnosticar** falhas de conexão
- **Validar** que sua implementação cliente está correta
- **Aprender** vendo frames reais

### 8.11.2 Filtros úteis

| Filtro                      | Mostra                            |
|-----------------------------|------------------------------------|
| `tcp.port == 502`           | Tráfego Modbus TCP (porta padrão) |
| `tcp.port == 5020`          | Modbus em porta alternativa       |
| `ip.addr == 192.168.1.45`   | Tudo que envolve este IP          |
| `modbus`                    | Pacotes que o Wireshark identifica como Modbus |
| `tcp.flags.syn == 1`        | Tentativas de abrir conexão        |
| `tcp.flags.reset == 1`      | Conexões resetadas (erro!)        |

### 8.11.3 Lab proposto

No laboratório de Modbus TCP, **capture com Wireshark** uma transação completa e identifique:

1. O three-way handshake inicial
2. O frame Modbus dentro de TCP
3. A resposta do escravo
4. O fechamento (FIN/ACK)

---

## 8.12 NAT — Network Address Translation

NAT permite que **muitos dispositivos privados** compartilhem **um único IP público**. É como um porteiro:

```
   Internet (IP público 200.x.y.z)
            │
            ▼
       Roteador NAT
            │
       ─────┴─────────────
       │                  │
   PC1 (192.168.1.5)   PC2 (192.168.1.6)
```

Implicações para automação:

- Equipamentos em rede privada **não são alcançáveis** diretamente da Internet sem configuração.
- Para expor um servidor Modbus à Internet, é preciso **port forwarding** no roteador (**não recomendado** sem VPN/TLS).

---

## 8.13 Boas Práticas de Rede em Automação Industrial

1. **Separe a rede de automação** da rede corporativa. Use VLANs ou switches físicos diferentes.
2. **Use IPs estáticos** em equipamentos críticos. DHCP é conveniente mas pode causar surpresas.
3. **Documente** o mapa IP da planta. Tenha uma planilha sempre atualizada.
4. **Reserve faixas** para tipos de equipamentos: ex., 192.168.10.x = CLPs, 192.168.20.x = HMIs, 192.168.30.x = sensores.
5. **Use switches gerenciáveis** para diagnóstico (port mirroring, SNMP).
6. **Time servers** (NTP) — sincronize relógios. Importantes para logs.
7. **Considere segurança** desde o início. Modbus TCP **não tem autenticação nativa** — use VPN, firewall, ou Modbus Secure.

---

## 8.14 Exercícios

### Conceituais

1. Por que dividir uma rede em camadas? Qual o benefício prático para o desenvolvedor de protocolos?
2. Diferencie TCP de UDP. Por que Modbus escolheu TCP?
3. O que é uma porta? Por que ela existe?

### Cálculos e análise

4. Você tem o IP **10.1.5.42** com máscara **255.255.0.0**. Qual é a rede? Qual o broadcast? Quantos hosts a rede comporta?
5. Dois PCs:
   - PC1: 192.168.1.10/24
   - PC2: 192.168.1.150/24
   Estão na mesma rede? Como tem certeza?
6. PC1 (192.168.1.10/24) e PC2 (192.168.2.10/24). Mesma rede? Como se comunicariam?

### Diagnóstico

7. Em uma planta, você consegue **pingar** o IP de um inversor mas a comunicação Modbus TCP falha. Liste 4 hipóteses e como investigar cada uma.
8. O comando `netstat -an | findstr LISTENING` retorna que a porta 502 não está aberta no servidor. O que está acontecendo? Como confirmar?
9. **Pesquisa.** Instale Wireshark e capture o tráfego de uma comunicação Modbus TCP entre dois dispositivos. Aponte:
   - O SYN inicial
   - O frame Modbus (use filtro `modbus`)
   - O ACK de resposta
   - Tempo total da transação

### Aplicação

10. Você precisa configurar 30 medidores de energia em uma planta. Proponha:
    - Faixa de IP a usar
    - Máscara
    - Gateway
    - Esquema de numeração (medidor 1 → IP 192.168.10.1, ou outra organização)
    - Como você documentaria isso?
11. **Em laboratório:** abra o cmd do Windows e identifique seu IP, máscara, gateway. Em seguida, execute `ping`, `tracert`, `arp -a` e `netstat -an`. Documente as saídas.

### Reflexão

12. Por que Modbus TCP usa a porta 502 e não a 80 (HTTP) ou 443 (HTTPS)?
13. Discuta os riscos de segurança de expor uma porta Modbus 502 diretamente à Internet. Que medidas adotaria para mitigar?

---

## 8.15 Síntese

- TCP/IP é estruturado em **camadas independentes**.
- **IP** endereça **logicamente** (32 bits IPv4).
- **TCP** garante entrega **fim a fim**.
- **Sockets** = (IP, porta, protocolo).
- **Modbus TCP** usa **porta 502** (TCP).
- Comandos `ping`, `ipconfig`, `arp`, `netstat`, `tracert` são suas ferramentas diárias.
- **Wireshark** é seu olho na rede.

---

## 8.16 Leitura recomendada para o próximo módulo

- **Modbus Organization** — *Modbus Messaging on TCP/IP Implementation Guide V1.0b*
- Revisar:
  - Como TCP segmenta e ordena pacotes
  - O conceito de **socket** em sua linguagem favorita (Python, C, Node.js)

---

**Próximo módulo:** [09-modbus-tcp.md](09-modbus-tcp.md)
