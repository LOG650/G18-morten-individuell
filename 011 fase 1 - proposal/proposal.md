# Proposal LOG650 – Forskningsprosjekt

**Student:** Morten Eidsvåg  
**Arbeidsform:** Individuelt

Jeg har valgt å gjennomføre dette prosjektet individuelt. Bakgrunnen for dette valget er at jeg benytter problemstilling og datagrunnlag fra bedriften jeg jobber i, og at jeg har god kjennskap til både organisasjonen og de logistiske problemstillingene som analyseres. Videre har jeg tilgang til relevante fagpersoner i virksomheten, blant annet Head of Supply Chain og salgssjef, som kan bidra med faglige avklaringer rundt datagrunnlag ved behov.

---

**Område:**

Etterspørselsprognoser – Hva blir salget neste måned? – Predikere fremtidig etterspørsel basert på historiske data, trender og sesongvariasjoner.

**Bedrift:** Anonymisert

Jeg arbeider i et legemiddelfirma som leverer varer fra et europeisk sentrallager til flere grossister i Norge. Bedriftens navn og produkter er anonymisert for å sikre tilgang til reelle data og for å ivareta konfidensialitet.

---

## Problemstilling

Den overordnede problemstillingen i prosjektet er:

**Hvilke prognosemodeller egner seg best for månedlige leveranser av farmasøytiske varelinjer i et sentrallager–grossist-system, og i hvilken grad varierer modellprestasjonene på tvers av produktsegmenter?**

For å besvare problemstillingen operasjonaliseres den gjennom tre forskningsspørsmål:

1. Hvilken av de fire modellene — naiv sesongprognose, Holt–Winters, ARIMA/SARIMA og XGBoost — gir lavest prognosefeil i testperioden, målt på tvers av alle SKU-er?
2. Varierer den relative modellprestasjonen mellom produktsegmenter, slik som høy- og lavvolum-SKU-er eller SKU-er med og uten tydelig sesongmønster?
3. I hvilken grad gir økt modellkompleksitet reell merverdi i en operasjonell planleggingskontekst?

---

## Datagrunnlag

Datagrunnlaget består av anonymiserte, månedlige volumdata for 105 varelinjer over en periode på 48 måneder (januar 2022 – desember 2025). Tallene representerer antall pakninger levert fra sentrallager til grossister, og gir et realistisk bilde av faktisk logistisk etterspørsel. De første 36 månedene benyttes til modelltrening, og de siste 12 månedene til testing, noe som gir om lag 5 040 observasjoner totalt.

Virksomheten har strenge retningslinjer for bruk av data i KI-verktøy og språkmodeller. Alle data som benyttes i prosjektet er derfor anonymisert, og brukes utelukkende til analyseformål innenfor rammen av dette studiet.

Datasettet kjennetegnes av høy andel nullverdier og varierende grad av sesongvariasjon mellom ulike varelinjer, noe som gjør det egnet til å sammenligne prognosemodeller under realistiske og utfordrende betingelser.

---

## Beslutningsvariabler: Metodisk tilnærming

**Naiv prognose som referansepunkt**

Den naive prognosen benyttes som referansepunkt for evaluering av mer avanserte metoder. Formålet er ikke høy presisjon, men å etablere et minimumsnivå som andre prognosemodeller bør kunne forbedre. Dersom en mer kompleks metode ikke gir bedre resultater enn den naive prognosen, vil det være vanskelig å forsvare bruken av den i praksis.

**Holt–Winters som klassisk statistisk metode**

Holt–Winters-metoden er inkludert fordi den er mye brukt i praksis for månedlige salgstall og er særlig godt egnet når etterspørselen viser både trend og sesongmønstre. I datagrunnlaget som analyseres finnes det ingen kampanjer, men det forekommer varierende grad av sesongvariasjon mellom ulike varelinjer.

**ARIMA/SARIMA som alternativ statistisk metode**

ARIMA/SARIMA er inkludert for å representere autoregressive metoder som kan fange opp autokorrelasjon og sesongmønstre. Metoden sammenlignes med Holt–Winters for å undersøke om mer avansert tidsseriemodellering gir merverdi.

**XGBoost som KI-basert sammenligningsverktøy**

Det er ønskelig fra bedriften jeg jobber i at prosjektet inkluderer en KI-basert tilnærming. XGBoost er valgt som gradientboostingmodell og trenes globalt på tvers av alle SKU-er (pooling). Formålet er ikke å erstatte etablerte prognosemetoder, men å undersøke om KI kan bidra med merverdi som supplement eller sammenligningsgrunnlag.

---

## Målfunksjon

Alle prognosemetodene vurderes ved hjelp av samme evalueringsopplegg, med felles feilmål og identiske datasett og prognosehorisonter. Det benyttes tre standard feilmål for å sikre sammenlignbarhet:

- **RMSE** – vektlegger store avvik og er sensitiv for uteliggere.
- **MAE** – gir et robust absolutt mål som er lettere å tolke operasjonelt.
- **MAPE** – muliggjør sammenligning på tvers av SKU-er med ulik volumskala.

Metodene evalueres på samme historiske datagrunnlag og samme prognoseperiode. Det anses som fullt akseptabelt at mer avanserte metoder gir marginal forbedring eller tilsvarende presisjon sammenlignet med enklere modeller. Økt kompleksitet gir ikke nødvendigvis økt praktisk nytte, og dette vil bli diskutert i prosjektet.

---

## Avgrensninger

Oppgaven avgrenses til analyse av anonymiserte, månedlige volumdata for 105 varelinjer levert fra sentrallager til grossister over en periode på 48 måneder (36 måneder trening, 12 måneder testing). Analysen setter søkelys på kortsiktige etterspørselsprognoser — én måneds prognosehorisont — ved bruk av fire modeller: naiv sesongprognose, Holt–Winters, ARIMA/SARIMA og XGBoost.

Oppgaven inkluderer ikke prisdata, kampanjer, demografiske variabler eller sluttkundesalg. Prognoser utvikles på varelinjenivå (SKU-nivå); aggregering til produkt- eller kategorinivå er ikke vurdert. Studien er basert på ett datasett fra én virksomhet, og funnene er ikke direkte generaliserbare til andre bransjer eller distribusjonskontekster.

---

Dette proposal er laget blant annet med teori fra kompendium i LOG650. Kvantitative metoder i logistikk — implementert via KI. ChatGPT er brukt for å vurdere datagrunnlaget opp mot teori. Den har kommet med flere løsningsforslag, men det er jeg som har valgt metode utfra det vi har lært i teorien.
