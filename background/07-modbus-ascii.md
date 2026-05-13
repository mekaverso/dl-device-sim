# Módulo 7 — Modbus ASCII: A Variante Textual

> *"Curto, simples e cada vez mais raro. Mas ainda existe — e por bons motivos históricos."*

## Objetivos de aprendizagem

Ao final deste módulo, o aluno será capaz de:

1. Descrever a codificação ASCII do Modbus e as diferenças em relação ao RTU.
2. Calcular o LRC (Longitudinal Redundancy Check) de um frame.
3. Identificar cenários onde Modbus ASCII ainda é justificável.
4. Converter mentalmente um frame entre ASCII e RTU.

---

## 7.1 Por Que Existe Modbus ASCII?

Em 1979, quando o Modbus foi criado, **muitos terminais e modems** trabalhavam **apenas com caracteres ASCII imprimíveis**. Modems não eram transparentes a 8 bits binários — alguns interpretavam certos bytes como comandos de controle, outros não toleravam caracteres com bit 7 ligado.

A solução foi simples: **codificar cada byte do frame como dois caracteres ASCII hexadecimais**. Assim, o byte 0xB4 vira `"B4"` no fio. Apenas caracteres `0–9`, `A–F`, `:`, CR, LF são transmitidos.

> Hoje, com modems e canais transparentes, a justificativa original sumiu. Modbus ASCII sobreviveu apenas em:
> - Sistemas legados que nunca foram atualizados
> - Comunicação através de **rádios** (alguns sistemas SCADA antigos)
> - **Diagnóstico**: é mais fácil ler um frame ASCII em um logger
> - **Robustez** em links muito ruidosos (caracteres impressos são mais "claros")

---

## 7.2 Estrutura do Frame

```
   ┌──────┬────────────┬────────────┬──────────────┬──────┬───────┬─────┐
   │  :   │ Slave Addr │ Function   │   Data       │ LRC  │  CR   │ LF  │
   │ 1 ch │   2 chars  │   2 chars  │  2×N chars   │ 2 ch │ 1 ch  │ 1 ch│
   └──────┴────────────┴────────────┴──────────────┴──────┴───────┴─────┘
```

| Campo         | Conteúdo                                                       |
|---------------|----------------------------------------------------------------|
| `:` (0x3A)    | Caractere de início                                            |
| Slave Address | Dois dígitos hex em ASCII (ex.: "01")                          |
| Function Code | Dois dígitos hex em ASCII (ex.: "04")                          |
| Data          | 2 caracteres por byte de dado                                  |
| LRC           | Dois dígitos hex em ASCII                                      |
| CR (0x0D)     | Carriage Return                                                |
| LF (0x0A)     | Line Feed                                                      |

### 7.2.1 Comparação com RTU

| Aspecto                | RTU                | ASCII                       |
|------------------------|--------------------|-----------------------------|
| Codificação            | Binária            | Caracteres ASCII hex        |
| Tamanho por byte de dado | 1 byte           | **2 caracteres** (2 bytes)  |
| Delimitador início     | Silêncio 3,5T      | `:`                         |
| Delimitador fim        | Silêncio 3,5T      | CR+LF                       |
| Verificação            | CRC-16             | LRC (8 bits)                |
| Tempo entre caracteres | Pode ser longo, sem timeout estrito | Limitado a 1 segundo |
| Sensibilidade a timing | **Alta**           | **Baixa**                   |

> **Vantagem do ASCII:** como o frame é delimitado por `:` e CR/LF, **não há restrição rigorosa de timing**. Caracteres podem chegar com pausas de até 1 segundo entre eles sem corromper o frame.
>
> **Desvantagem:** o overhead é o **dobro** do RTU (cada byte vira 2 caracteres).

---

## 7.3 LRC — Longitudinal Redundancy Check

O **LRC** é um checksum mais simples que o CRC-16. Ele tem **8 bits** apenas.

### 7.3.1 Algoritmo

```
   1. Soma todos os bytes do frame (exceto :, LRC, CR, LF) — antes da codificação ASCII!
   2. Pega os 8 bits menos significativos da soma
   3. Calcula o complemento de dois (negação binária + 1)
   4. Codifica o resultado como 2 caracteres ASCII hex
```

### 7.3.2 Em Python

```python
def lrc(data: bytes) -> int:
    return ((-sum(data)) & 0xFF)

# Uso:
frame_bin = bytes([0x01, 0x04, 0x00, 0x00, 0x00, 0x02])
checksum = lrc(frame_bin)
# checksum = 0xF9
```

### 7.3.3 Em C

```c
uint8_t lrc(const uint8_t *data, size_t len) {
    uint8_t sum = 0;
    for (size_t i = 0; i < len; i++) sum += data[i];
    return (uint8_t)(-sum);
}
```

### 7.3.4 Exemplo

Frame Modbus (em bytes binários, equivalente RTU): `01 04 00 00 00 02`

- Soma: 0x01 + 0x04 + 0x00 + 0x00 + 0x00 + 0x02 = **0x07**
- Complemento de dois: ~0x07 + 1 = 0xF8 + 1 = **0xF9**
- LRC = 0xF9 → codificado como **"F9"** em ASCII

Frame ASCII completo:

```
   :01040000000 2F9\r\n
```

Em ASCII hexadecimal puro:

```
   3A 30 31 30 34 30 30 30 30 30 30 30 32 46 39 0D 0A
   :  0  1  0  4  0  0  0  0  0  0  0  2  F  9 CR LF
```

---

## 7.4 Comparação Direta — RTU vs. ASCII

Mesma transação: ler 2 input registers a partir do endereço 0 do escravo 1.

### Em RTU (8 bytes no fio)

```
   01 04 00 00 00 02 71 CB
```

### Em ASCII (17 bytes no fio)

```
   :01040000000 2F9\r\n
```

> **Em ASCII a transmissão demora exatamente o dobro** do tempo (mesmo baud rate). E o conteúdo informativo é o mesmo.

---

## 7.5 Em Que Cenário Modbus ASCII Ainda Faz Sentido?

1. **Equipamentos legados** que não foram atualizados (refinarias antigas, sistemas dos anos 80–90).
2. **Rádios** half-duplex onde o atraso entre caracteres é variável.
3. **Diagnóstico interativo** com terminal serial humano — é possível digitar um frame ASCII manualmente.
4. **Canais semi-confiáveis** onde a simplicidade do LRC e a redundância de codificação ASCII facilitam detecção visual.
5. **Modems via linha telefônica analógica** — raros, mas existem.

Em uma planta nova de 2026, **Modbus ASCII é evitado**. Mas você precisa conhecer porque ainda pode encontrá-lo em manutenção.

---

## 7.6 Limites Importantes

- **Sem broadcast** efetivo: o caractere `:` reseta o estado de qualquer escravo, mas isso é problema para implementações reais. Broadcast é raramente usado em ASCII.
- **Sensível a inserção de caracteres alienígenas**: se um byte espúrio aparece no meio, **todo o frame falha**.
- **CR/LF obrigatórios**: alguns equipamentos exigem o par CR+LF; outros aceitam só LF. Sempre verifique o manual.

---

## 7.7 Exercícios

### Cálculos

1. Calcule o LRC do frame Modbus equivalente a **05 06 00 64 00 C8**.
2. Codifique o frame acima em sua forma ASCII completa, incluindo `:` e CR/LF.
3. Quantos bytes no fio um frame Modbus ASCII consome em relação ao equivalente RTU? Mostre a fórmula geral.

### Interpretação

4. Você captura o seguinte fluxo ASCII (sem CR/LF visíveis):
   ```
   :010300000005F7
   ```
   - Qual o endereço do escravo?
   - Qual a função?
   - Qual o endereço inicial e quantidade?
   - Qual o LRC esperado e qual o transmitido?
5. Discuta: em uma rede com **alta latência variável** (rádio sem fio), por que Modbus ASCII é tecnicamente mais resiliente que Modbus RTU?

### Conversão

6. Converta o seguinte frame **RTU** para sua forma **ASCII**:
   ```
   03 06 00 0A 00 03 A8 7A
   ```
7. Converta o seguinte frame **ASCII** para sua forma **RTU**:
   ```
   :07040020000AF8
   ```

### Aplicação

8. **Pesquisa.** Encontre **um equipamento industrial atualmente vendido** que ainda suporte Modbus ASCII. Justifique por que ainda é oferecido.
9. **Reflexão.** Se você fosse desenvolvedor de firmware de um inversor, mantém suporte a Modbus ASCII em 2026? Justifique considerando custo de desenvolvimento, base de usuários e ROI.

---

## 7.8 Síntese

- Modbus ASCII codifica **cada byte como 2 caracteres ASCII hexadecimais**.
- Frame: `: addr fc data lrc CR LF`.
- LRC: complemento de dois da soma dos bytes (em sua forma binária pré-codificação).
- **Vantagem**: tolera timing relaxado, debug humano.
- **Desvantagem**: dobro de overhead.
- **Status em 2026**: raro, mas existe — saiba reconhecer e diagnosticar.

---

**Próximo módulo:** [08-fundamentos-tcp-ip.md](08-fundamentos-tcp-ip.md)
