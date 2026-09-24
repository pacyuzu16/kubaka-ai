# Kinyarwanda test cases — fill these in

**Your only job:** replace each `input` with how a Rwandan mechanic or operator would
ACTUALLY say it. My drafts below are guesses — correct them freely. Everything else
(id, gold labels) is already done.

Rules that make these valuable:
- Write it the way it is really said, not textbook Kinyarwanda
- Mixing in English or French words is GOOD (moteri, bateri, fureni, chenille)
- Short and vague is GOOD — real messages are 3-6 words
- If my draft is wrong or unnatural, rewrite it completely

When done, tell Claude and it will load them and re-run the evaluation.

---

### RW-005  —  *means:* engine overheating, coolant disappearing
- **gold:** `engine` / `eng_overheat` / `critical`
- **my draft:** moteri irashyuha cyane kandi amazi arigenda
- **your version:** moteri iri gushyuha cyane, amazi akonjyesha yagabanutse

### RW-006  —  *means:* black smoke from exhaust
- **gold:** `engine` / `eng_smoke` / `medium`
- **my draft:** imashini iravuza umwotsi wirabura
- **your version:** imashini iri kuzana umwotsi wumukara aho ihumekera

### RW-007  —  *means:* engine knocking loudly
- **gold:** `engine` / `eng_noise` / `critical`
- **my draft:** moteri irasakuza nk'ikintu kimenetse
- **your version:** moteri iri gusakuza cyane

### RW-008  —  *means:* loses power going uphill
- **gold:** `engine` / `eng_power` / `medium`
- **my draft:** ntabwo ifite imbaraga iyo nzamuka
- **your version:** ibura imbaraga iyo iri kuzamuka

### RW-009  —  *means:* track is too loose and slapping
- **gold:** `undercarriage` / `und_tension` / `medium`
- **my draft:** ibiziga (chenille) birekuye cyane
- **your version:** track iri gukoranaho

### RW-010  —  *means:* machine pulls to one side
- **gold:** `undercarriage` / `und_align` / `medium`
- **my draft:** imashini ijya ibumoso iyo ngenda
- **your version:** imishini iri gukorera kuruhande rumwe

### RW-011  —  *means:* battery flat every morning
- **gold:** `electrical` / `ele_charge` / `medium`
- **my draft:** bateri irangira buri joro
- **your version:** bateri ishiramo umuriro buri gitondo

### RW-012  —  *means:* burning smell, fuse blowing
- **gold:** `electrical` / `ele_wiring` / `high`
- **my draft:** numva impumuro y'ibyotswa
- **your version:** numva impumuro yo gutwika

### RW-013  —  *means:* display showing an error code
- **gold:** `electrical` / `ele_display` / `low`
- **my draft:** ikirahuri cy'imbere kigaragaza error
- **your version:** kuri sikirini hariho error (ikosa)

### RW-014  —  *means:* engine revs but machine barely moves
- **gold:** `transmission` / `trn_slip` / `high`
- **my draft:** moteri irazamuka ariko imashini ntigenda
- **your version:** moteri irakora ariko imashini ntigenda

### RW-015  —  *means:* brakes soft, long stopping distance
- **gold:** `transmission` / `trn_brake` / `critical`
- **my draft:** fureni ntizikora neza, bitinda guhagarara
- **your version:** fire ntizikomeye, ihagarara itinze

### RW-016  —  *means:* crack on the boom
- **gold:** `structure` / `str_crack` / `critical`
- **my draft:** hari agace kamenetse ku kuboko
- **your version:** hari agace kamenetse

### RW-017  —  *means:* bucket teeth worn flat
- **gold:** `structure` / `str_bucket` / `low`
- **my draft:** amenyo y'igikombe yashize
- **your version:** amenyo yangiritse

### RW-018  —  *means:* bucket sinks on its own when parked
- **gold:** `hydraulic` / `hyd_drift` / `critical`
- **my draft:** igikombe kimanuka cyonyine
- **your version:** agakombe karimanura iyo uhagaze

### RW-019  —  *means:* pump whining loudly
- **gold:** `hydraulic` / `hyd_noise` / `high`
- **my draft:** pompe iravuza cyane
- **your version:** pompe irikaraga maze igasakuza cyane
