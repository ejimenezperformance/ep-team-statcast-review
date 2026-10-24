# EP Team Statcast Review — Does a team's "luck gap" repeat? / ¿Se repite la "brecha de suerte" de un equipo?

**Emerson Jimenez · Emerson Performance (EP)** · EN / ES

> **Status: real 2025 and 2026 data run complete (30 teams). Headline: the pitching gap passed the frozen test, but an exploratory check says what repeats is mostly the ballpark, not team skill.**
> **Estado: corrida con datos reales 2025 y 2026 completa (30 equipos). Titular: la diferencia de pitcheo pasó la prueba congelada, pero una comprobación exploratoria indica que lo que se repite es sobre todo el estadio, no una habilidad del equipo.**

---

## English

### Decision question
For each of the 30 teams: did results (wOBA) come with more or less than the quality of contact (xwOBA) said they should, on offense and on pitching, **and does that gap repeat the next season?**
If it repeats, it looks like a team trait. If it does not, it was mostly luck, and a front office should not pay for it or fear it.

- Offense gap = wOBA − xwOBA. Pitching gap = wOBA against − xwOBA against.
- Universe: all 30 teams, regular season 2025 and 2026 (Statcast via `pybaseball`).
- Also reported per team (descriptive): xwOBA, barrel%, hard-hit%, K%, BB%, chase%, whiff%, bat speed and swing length (offense), four-seam velocity (pitching). See `outputs/team_cards_2026.md`.

### Frozen test (written before the code ran on real data)
- **CONFIRMED** (per side): Pearson r between the 2025 and 2026 gap across the 30 teams ≥ **0.30**, and the 95% bootstrap CI (resampling teams) above zero. Otherwise **NOT CONFIRMED**, and that result is published too.
- Secondary (descriptive): first-half vs. second-half persistence inside each season; and whether last year's wOBA or last year's xwOBA predicts this year's wOBA better (leave-one-team-out).

### How well can this test see a real effect? (synthetic leagues, known truth)
| True situation | Share of 300 synthetic leagues labeled CONFIRMED |
|---|---|
| Gap is a fully stable team trait | 92% |
| Gap is half trait, half luck | 40% |
| Gap is pure luck | 5.7% (false positives) |

So a null result here means "no evidence of a stable gap in two seasons", not "proof there is none". With only 30 teams and one year-to-year pair, a modest real effect can be missed.

### Limits (read before interpreting)
- **CONFIRMED / INTERPRETATION labels:** the numbers are `CONFIRMED` (they come from the data and the test). Anything about *why* a gap exists is `INTERPRETATION`. A gap "came with" contact quality; it does not show a cause.
- **League-wide offset:** almost every team has a positive gap in both years (league average about +0.008), because Statcast's xwOBA sits a little below actual wOBA for the whole league. Correlations are not affected, but a gap is only meaningful **relative to the league average**. Team cards and charts are centered that way (dashed lines).
- wOBA − xwOBA mixes several things: ballpark, defense, sequencing, and skills xwOBA does not capture (for example sprint speed on offense). This repo does not separate them.
- Rosters change between seasons, so team persistence is harder to see than player persistence.
- The batting team is derived from the half-inning (top = away bats); tested on synthetic data.
- Only two seasons, 30 teams. No starters/bullpen split, no park adjustment.

### Run it (Windows, from the inner project folder)
```
pip install -r requirements.txt
python tests/test_team_review.py
python src/data_loader.py 2025
python src/data_loader.py 2026
python src/run_team_analysis.py
```
Outputs: `outputs/summary.txt`, `outputs/team_gap_persistence_EN.png` / `_ES.png`, `outputs/team_gap_home_vs_road_EN.png` / `_ES.png`, `outputs/team_cards_2026.md`, team tables as CSV.

### Results (real data, 2025 → 2026, 30 teams)
**Headline: the pitching gap passed the frozen test, barely. An exploratory check then showed that the part that repeats lives in home games, so it looks like the ballpark, not team skill. The offense gap did not clear the frozen bar.**

| Side | r (2025 gap → 2026 gap) | 95% CI (resampling teams) | Frozen verdict |
|---|---|---|---|
| Offense (wOBA − xwOBA) | +0.26 | −0.04 to +0.55 | NOT CONFIRMED |
| Pitching (wOBA against − xwOBA against) | +0.40 | +0.01 to +0.65 | CONFIRMED |

- `CONFIRMED` is marginal for pitching: the CI floor is +0.01 and the Spearman correlation is +0.24. With 30 teams and two sides tested, read it as suggestive, not settled.
- Benchmarks: xwOBA itself repeats year to year (offense r = +0.44, pitching r = +0.63). Actual wOBA repeats less on offense (+0.14) and about as much on pitching (+0.61).
- Last year's xwOBA did not predict this year's wOBA measurably better than last year's wOBA (RMSE gain −0.0000 on offense, −0.0007 on pitching; both CIs include zero). With 30 teams this test cannot separate them.
- Inside each season (first half vs. second half, descriptive): offense +0.34 (2025) and +0.37 (2026); pitching +0.42 (2025) and +0.54 (2026). The 2026 intervals are above zero on both sides; the 2025 intervals include zero.
- **Exploratory check, decided after seeing the main result** (so it does not count toward CONFIRMED): the same correlation using only home games, only road games, and all games without COL and ATH (the two most extreme parks).

| Side | Home games only | Road games only | All games, without COL and ATH |
|---|---|---|---|
| Offense | +0.41 [+0.06, +0.67] | +0.11 [−0.23, +0.43] | +0.19 [−0.16, +0.51] |
| Pitching | +0.58 [+0.23, +0.77] | −0.05 [−0.37, +0.30] | +0.17 [−0.21, +0.49] |

  Home and road use the same number of games, so they are comparable. The home-versus-road difference was not formally tested (the intervals partly overlap), and the road halves are noisier.
- `INTERPRETATION`: the pattern fits a ballpark effect. xwOBA ignores the park, a team keeps the same park every year, and the gap that repeats shows up at home and fades on the road and without the two extreme parks. Defense and sequencing can also repeat, and this repo does not separate them. Practical reading: do not read wOBA − xwOBA as team luck or skill without a park adjustment; most of the part that repeats looks like the park.

### Audit log
| # | What was found | What changed |
|---|---|---|
| 1 | Two synthetic tests had wrong expected values (whiff% count; bat-speed mean). The code was right. | Corrected the tests, not the code. |
| 2 | A planted-gap end-to-end test was too weak for one noisy simulated season. | Larger planted gap; added a check against the planted truth. |
| 3 | The first real-data chart and cards treated zero as "no gap", but the whole league sits near +0.008, so nearly every team looked "above" its contact quality. | Cards and charts now compare each team with the league average; two new checks. Correlations were never affected. |

---

## Español

### Pregunta de decisión
Para cada uno de los 30 equipos: ¿los resultados (wOBA) vinieron por encima o por debajo de lo que decía la calidad de contacto (xwOBA), en ofensiva y en pitcheo, **y esa diferencia se repite al año siguiente?**
Si se repite, parece un rasgo del equipo. Si no, fue sobre todo suerte, y una oficina no debería pagar por eso ni temerlo.

- Diferencia ofensiva = wOBA − xwOBA. Diferencia de pitcheo = wOBA en contra − xwOBA en contra.
- Universo: los 30 equipos, temporada regular 2025 y 2026 (Statcast con `pybaseball`).
- También por equipo (descriptivo): xwOBA, barrel%, hard-hit%, K%, BB%, chase%, whiff%, velocidad de bate y largo del swing (ofensiva), velocidad de la recta de cuatro costuras (pitcheo). Ver `outputs/team_cards_2026.md`.

### Prueba congelada (escrita antes de correr el código con datos reales)
- **CONFIRMADO** (por lado): correlación de Pearson entre la diferencia 2025 y la de 2026 en los 30 equipos ≥ **0.30**, y el IC 95% por bootstrap (remuestreando equipos) por encima de cero. Si no, **NO CONFIRMADO**, y ese resultado también se publica.
- Secundario (descriptivo): persistencia entre primera y segunda mitad de cada temporada; y si el wOBA o el xwOBA del año pasado predice mejor el wOBA de este año (dejando un equipo fuera).

### ¿Cuánto puede ver esta prueba un efecto real? (ligas sintéticas con verdad conocida)
| Situación verdadera | Ligas sintéticas marcadas CONFIRMADO (de 300) |
|---|---|
| La diferencia es un rasgo estable del equipo | 92% |
| Mitad rasgo, mitad suerte | 40% |
| Pura suerte | 5.7% (falsos positivos) |

Un resultado nulo aquí significa "no hay evidencia de una diferencia estable en dos temporadas", no "está probado que no existe". Con 30 equipos y un solo par de años, un efecto real moderado puede pasar desapercibido.

### Límites (leer antes de interpretar)
- **Etiquetas CONFIRMADO / INTERPRETACIÓN:** los números son `CONFIRMADO` (salen de los datos y la prueba). Todo lo que explique *por qué* existe una diferencia es `INTERPRETACIÓN`. La diferencia "vino con" la calidad de contacto; no demuestra una causa.
- **Desplazamiento de toda la liga:** casi todos los equipos tienen una diferencia positiva en ambos años (promedio de la liga cerca de +0.008), porque el xwOBA de Statcast queda un poco por debajo del wOBA real para toda la liga. Las correlaciones no se afectan, pero una diferencia solo tiene sentido **frente al promedio de la liga**. Las fichas y los gráficos están centrados así (líneas punteadas).
- wOBA − xwOBA mezcla varias cosas: estadio, defensa, secuencia y habilidades que el xwOBA no captura (por ejemplo velocidad de carrera en ofensiva). Este repo no las separa.
- Las plantillas cambian entre temporadas, así que la persistencia por equipo es más difícil de ver que la de jugadores.
- El equipo al bate se deriva de la media entrada (alta = batea el visitante); probado con datos sintéticos.
- Solo dos temporadas y 30 equipos. Sin separar abridores y bullpen, sin ajuste por estadio.

### Cómo correrlo (Windows, desde la carpeta interna del proyecto)
Los mismos cinco comandos de arriba, en ese orden.

### Resultados (datos reales, 2025 → 2026, 30 equipos)
**Titular: la diferencia de pitcheo pasó la prueba congelada, por poco. Una comprobación exploratoria mostró después que lo que se repite vive en los partidos en casa, así que parece el estadio, no una habilidad del equipo. La de ofensiva no pasó el umbral congelado.**

| Lado | r (diferencia 2025 → diferencia 2026) | IC 95% (remuestreando equipos) | Veredicto congelado |
|---|---|---|---|
| Ofensiva (wOBA − xwOBA) | +0.26 | −0.04 a +0.55 | NO CONFIRMADO |
| Pitcheo (wOBA en contra − xwOBA en contra) | +0.40 | +0.01 a +0.65 | CONFIRMADO |

- El `CONFIRMADO` de pitcheo es marginal: el piso del IC es +0.01 y la correlación de Spearman es +0.24. Con 30 equipos y dos lados probados, léelo como una señal sugerente, no como algo establecido.
- Referencias: el xwOBA en sí se repite de un año a otro (ofensiva r = +0.44, pitcheo r = +0.63). El wOBA real se repite menos en ofensiva (+0.14) y casi igual en pitcheo (+0.61).
- El xwOBA del año pasado no predijo el wOBA de este año de forma medible mejor que el wOBA del año pasado (mejora de RMSE −0.0000 en ofensiva, −0.0007 en pitcheo; ambos IC incluyen cero). Con 30 equipos esta prueba no los puede separar.
- Dentro de cada temporada (primera vs. segunda mitad, descriptivo): ofensiva +0.34 (2025) y +0.37 (2026); pitcheo +0.42 (2025) y +0.54 (2026). Los intervalos de 2026 quedan por encima de cero en ambos lados; los de 2025 incluyen el cero.
- **Comprobación exploratoria, decidida después de ver el resultado principal** (por eso no cuenta para CONFIRMADO): la misma correlación usando solo partidos en casa, solo de visitante, y todos los partidos sin COL ni ATH (los dos estadios más extremos).

| Lado | Solo en casa | Solo de visitante | Todos, sin COL ni ATH |
|---|---|---|---|
| Ofensiva | +0.41 [+0.06, +0.67] | +0.11 [−0.23, +0.43] | +0.19 [−0.16, +0.51] |
| Pitcheo | +0.58 [+0.23, +0.77] | −0.05 [−0.37, +0.30] | +0.17 [−0.21, +0.49] |

  Casa y visitante usan la misma cantidad de partidos, así que son comparables. La diferencia entre casa y visitante no se probó formalmente (los intervalos se solapan en parte), y las mitades de visitante tienen más ruido.
- `INTERPRETACIÓN`: el patrón encaja con un efecto de estadio. El xwOBA ignora el estadio, un equipo conserva el mismo estadio cada año, y la diferencia que se repite aparece en casa y se desvanece de visitante y sin los dos estadios extremos. La defensa y la secuencia también pueden repetirse, y este repo no las separa. Lectura práctica: no leas wOBA − xwOBA como suerte o habilidad del equipo sin un ajuste por estadio; la mayor parte de lo que se repite parece ser el estadio.

### Registro de correcciones
| # | Qué se encontró | Qué cambió |
|---|---|---|
| 1 | Dos pruebas sintéticas tenían valores esperados incorrectos (conteo de whiff%; promedio de velocidad de bate). El código estaba bien. | Se corrigieron las pruebas, no el código. |
| 2 | Una prueba de extremo a extremo con diferencia plantada era demasiado débil para una temporada simulada con ruido. | Diferencia plantada mayor; se agregó una verificación contra la verdad plantada. |
| 3 | El primer gráfico y las fichas con datos reales tomaban el cero como "sin diferencia", pero toda la liga está cerca de +0.008, así que casi todos los equipos parecían "por encima" de su calidad de contacto. | Las fichas y los gráficos ahora comparan cada equipo con el promedio de la liga; dos pruebas nuevas. Las correlaciones nunca se afectaron. |

---
*Part of the EP analytics portfolio · https://ejimenezperformance.github.io*
