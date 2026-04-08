# SpaceEngine 천체 이름 레퍼런스

> SE 카탈로그(Catalogs.pak)에서 추출한 실제 사용 가능한 천체 이름.
> 스크립트에서 `Select "이름"` 명령에 사용할 수 있습니다.
>
> **참고**: `/`로 구분된 이름은 동일 천체의 별칭(alias)입니다.
> 첫 번째 이름이 기본 표시 이름이며, 모든 별칭으로 접근 가능합니다.

---

## 카탈로그 파일 구조 요약

| 파일 | 내용 | 항목 수 |
|------|------|---------|
| `planets/SolarSys.sc` | 태양계 (항성, 행성, 위성, 왜소행성) | 56 |
| `stars/HIPPARCOS.csv` | HIPPARCOS 항성 카탈로그 | ~112,500 |
| `stars/Stars.sc` | 주요 항성 (수정/추가) | 77 (Star + StarBarycenter) |
| `stars/Stars-fix.sc` | 항성 데이터 수정 | 123 |
| `stars/ExoPlanetsSuns.sc` | 외계행성 모항성 | 2,476 |
| `stars/WhiteDwarfs.sc` | 백색왜성 | 3,648 |
| `stars/NeutronStars.sc` | 중성자별 (펄서) | 2,034 (+ 2,034 Barycenter) |
| `stars/BrownDwarfs.sc` | 갈색왜성 | 4,504 |
| `stars/BlackHoles.sc` | 블랙홀 (항성질량) | 129 Star + 43 StarBarycenter |
| `planets/ExoPlanets.sc` | 외계행성 (1차) | 3,488 |
| `planets/ExoPlanets2.sc` | 외계행성 (2차) | 2,523 |
| `planets/ExoPlanets-custom.sc` | 외계행성 (커스텀/주요) | 49 Planet + 2 Moon |
| `planets/Asteroids.sc` | 소행성 | 35 |
| `planets/KuiperBelt.sc` | 카이퍼 벨트 천체 | 69 Asteroid + 2 Comet |
| `planets/Comets.sc` | 혜성 | 284 |
| `planets/NeutronStars.sc` | 중성자별 행성계 | 2,034 |
| `planets/BlackHoles.sc` | 블랙홀 동반성 | 81 |
| `nebulae/SpriteAstro.sc` | 성운 (Astro 스프라이트) | 15 |
| `nebulae/SpriteBambus.sc` | 성운 (Bambus 스프라이트) | 95 |
| `nebulae/SpriteVoe.sc` | 성운 (Voe 스프라이트) | 8 |
| `nebulae/RaymarchBambus.sc` | 성운 (Bambus 레이마치) | 20 |
| `nebulae/RaymarchPhunnie.sc` | 성운 (Phunnie 레이마치) | 2 |
| `nebulae/Planetary.sc` | 행성상 성운 | 50 |
| `nebulae/Extragalactic.sc` | 외부은하 성운 | 1 |
| `nebulae/SpaceEngine.sc` | 커스텀 성운 | 1 |
| `galaxies/LocalGroup.sc` | 국부은하군 은하 | 47 |
| `galaxies/Galaxies.sc` | 주요 은하 | 25 |
| `galaxies/Kexitt.sc` | 추가 은하 | 89 |
| `galaxies/BlackholeHosts.sc` | 블랙홀 모은하 | 73 |
| `galaxies/NGC-IC.csv` | NGC/IC 은하 카탈로그 | ~10,843 |
| `clusters/Globular.sc` | 구상성단 | 154 |
| `clusters/Open.sc` | 산개성단 | 1,115 |
| `clusters/Extragalactic.sc` | 외부은하 성단 | 9 |

---

## 태양계 (SolarSys.sc)

### 항성
- `Sun` (별칭: `Sol`)

### 행성
- `Mercury`
- `Venus`
- `Earth`
- `Mars`
- `Jupiter`
- `Saturn`
- `Uranus`
- `Neptune`

### 중심좌표계 (Barycenter)
- `Earth-Moon`
- `Pluto-Charon`

### 왜소행성
- `Ceres` (별칭: `(1) Ceres`)
- `Pluto` (별칭: `(134340) Pluto`)
- `Haumea` (별칭: `(136108) Haumea`, `2003 EL61`)
- `Quaoar` (별칭: `(50000) Quaoar`)
- `Makemake` (별칭: `(136472) Makemake`, `2005 FY9`)
- `Eris` (별칭: `(136199) Eris`, `2003 UB313`)

### 주요 위성 (Moon)
- `Moon` (별칭: `Earth I`)
- `Io` (별칭: `Jupiter I`)
- `Europa` (별칭: `Jupiter II`)
- `Ganymede` (별칭: `Jupiter III`)
- `Callisto` (별칭: `Jupiter IV`)
- `Mimas` (별칭: `Saturn I`)
- `Enceladus` (별칭: `Saturn II`)
- `Tethys` (별칭: `Saturn III`)
- `Dione` (별칭: `Saturn IV`)
- `Rhea` (별칭: `Saturn V`)
- `Titan` (별칭: `Saturn VI`)
- `Iapetus` (별칭: `Saturn VIII`)
- `Miranda` (별칭: `Uranus V`)
- `Ariel` (별칭: `Uranus I`)
- `Umbriel` (별칭: `Uranus II`)
- `Titania` (별칭: `Uranus III`)
- `Oberon` (별칭: `Uranus IV`)
- `Proteus` (별칭: `Neptune VIII`, `S|1989 N1`)
- `Triton` (별칭: `Neptune I`)
- `Charon` (별칭: `Pluto I`)
- `Dysnomia` (별칭: `Eris I`)

### 소형 위성 (DwarfMoon)
- `Phobos` (별칭: `Mars I`)
- `Deimos` (별칭: `Mars II`)
- `Amalthea` (별칭: `Jupiter V`)
- `Hyperion` (별칭: `Saturn VII`)
- `Phoebe` (별칭: `Saturn IX`)
- `Nereid` (별칭: `Neptune II`)
- `Styx` (별칭: `Pluto V`)
- `Nix` (별칭: `Pluto II`)
- `Kerberos` (별칭: `Pluto IV`)
- `Hydra` (별칭: `Pluto III`)
- `Hi'iaka` (별칭: `Haumea I`)
- `Namaka` (별칭: `Haumea II`)
- `Weywot` (별칭: `(50000) Quaoar I Weywot`)
- `S|2015 (136472) 1` (별칭: `MK 2`)

### 소행성 (SolarSys.sc 내)
- `Pallas` (별칭: `(2) Pallas`)
- `Juno` (별칭: `(3) Juno`)
- `Vesta` (별칭: `(4) Vesta`)
- `Hygiea` (별칭: `(10) Hygiea`)

---

## 주요 항성 (HIPPARCOS.csv)

HIPPARCOS 카탈로그는 ~112,500개의 항성을 포함하며, CSV 형식입니다.
형식: `Name,RA,Dec,Dist,AppMagn,SpecClass,MassSol,RadSol,Temperature`

### 유명 항성 (HIPPARCOS 카탈로그에서 확인된 정확한 이름)
| SE 기본 이름 | 전체 카탈로그 이름 |
|---|---|
| `Sirius` | `Sirius/Alhabor/ALF CMa/9 CMa/Gliese 244/HIP 32349/HD 48915` |
| `Canopus` | `Canopus/Suhel/ALF Car/HIP 30438/HD 45348` |
| `Arcturus` | `Arcturus/ALF Boo/16 Boo/HIP 69673/HD 124897` |
| `Vega` | `Vega/ALF Lyr/3 Lyr/Gliese 721/HIP 91262/HD 172167` |
| `Capella` | `Capella/Alhajot/ALF Aur/13 Aur/HIP 24608/HD 34029` |
| `Rigel` | `Rigel/BET Ori/19 Ori/HIP 24436/HD 34085` |
| `Procyon` | `Procyon/Elgomaisa/ALF CMi/10 CMi/Gliese 280/HIP 37279/HD 61421` |
| `Achernar` | `Achernar/ALF Eri/HIP 7588/HD 10144` |
| `Aldebaran` | `Aldebaran/Oculus Tauri/ALF Tau/87 Tau/HIP 21421/HD 29139` |
| `Spica` | `Spica/Azimech/ALF Vir/67 Vir/HIP 65474/HD 116658` |
| `Antares` | `Antares/Calbalacrab/ALF Sco/21 Sco/HIP 80763/HD 148478` |
| `Fomalhaut` | `Fomalhaut/ALF PsA/24 PsA/Gliese 881/HIP 113368/HD 216956` |
| `Deneb` | `Deneb/ALF Cyg/50 Cyg/HIP 102098/HD 197345` |
| `Regulus` | `Regulus/Kabeleced/Cor Leonis/Kalb/ALF Leo/32 Leo/HIP 49669/HD 87901` |
| `Polaris` | `Polaris/Alrukaba/ALF UMi/1 UMi/HIP 11767/HD 8890` |
| `Proxima` | `Proxima/Proxima Cen/ALF Cen C/V645 Cen/Gliese 551/HIP 70890` |
| `ALF Cen A` | `ALF Cen A/ALF1 Cen/Toliman A/Rigel Kentaurus A/Gliese 559 A/HIP 71683/HD 128620` |
| `ALF Cen B` | `ALF Cen B/ALF2 Cen/Toliman B/Rigel Kentaurus B/Gliese 559 B/HIP 71681/HD 128621` |
| `Barnard's Star` | `Barnard's Star/Munich 15040/Gliese 699/HIP 87937` |
| `TAU Cet` | `TAU Cet/52 Cet/Gliese 71/HIP 8102/HD 10700` |
| `EPS Eri` | `EPS Eri/18 Eri/Gliese 144/HIP 16537/HD 22049` |
| `Ross 128` | `Ross 128/FI Vir/Gliese 447/HIP 57548` |
| `Ross 154` | `Ross 154/V1216 Sgr/Gliese 729/HIP 92403` |
| `Denebola` | `Denebola/BET Leo/94 Leo/HIP 57632/HD 102647` |
| `Lalande 21185` | `HD 95735/Lalande 21185/Gliese 411/HIP 54035` |

> **참고 - Sirius B**: Sirius는 단일 항목으로 등록됩니다. Sirius B는
> 별도의 .sc 파일(Stars-bin.sc)에서 정의될 수 있습니다.
> Select 명령 시에는 `"Sirius"` 또는 `"ALF CMa"`를 사용하세요.

> **참고 - Proxima Centauri**: 정확한 카탈로그 이름은 `"Proxima"` 또는
> `"Proxima Cen"` 또는 `"ALF Cen C"`입니다. 모두 동일한 천체를 가리킵니다.

---

## Stars.sc 추가 항성 (특수 항성)

Stars.sc는 HIPPARCOS에 없는 특수 항성이나 수정이 필요한 항성을 정의합니다.

### 거성/극대거성
- `Betelgeuse` (별칭: `Betelgeuze/ALF Ori/58 Ori/HIP 27989/HD 39801`)
- `VY CMa` (별칭: `HD 58061/HIP 35793`)
- `UY Sct`
- `Stephenson 2-18` (별칭: `Stephenson 2 DFK 1/RSGC2-18`)
- `NML Cyg` (별칭: `V1489 Cyg`)
- `KY Cyg`
- `KW Sgr` (별칭: `HD 316496/HIP 87433`)
- `VX Sgr` (별칭: `HIP 88838/HD 165674`)
- `AH Sco` (별칭: `HIP 84071/HD 155161`)
- `PZ Cas` (별칭: `HIP 117078`)
- `WOH G64`
- `W1-26` (별칭: `W26/Wd 1-26/Westerlund 1-26`)

### 특이 항성
- `Pistol Star` (별칭: `V4647 Sgr`)
- `La Superba` (별칭: `Y CVn/HD 110914/HIP 62223`)
- `V838 Mon` (별칭: `Nova Monocerotis 2002`)
- `S Dor` (별칭: `HD 35343`)
- `WR 25` (별칭: `HD 93162`)
- `Kapteyn` (별칭: `Kapteyn's Star/VZ Pic/Gliese 191/GJ 191/HD 33793/HIP 24186`)
- `UDF 2457` (별칭: `GOODS-MUSIC 9034`)
- `Mamajek's Object` (별칭: `V1400 Cen/1SWASP J1407/J1407`)

### 복합 항성계 (StarBarycenter)
- `Solar System`
- `R136a1 system`
- `Alcyone` (별칭: `ETA Tau/25 Tau/HIP 17702/HD 23630`)
- `Altair` (별칭: `ALF Aql/53 Aql/Gliese 768/HIP 97649/HD 187642`)
- `Vega` (별칭: `ALF Lyr/3 Lyr/Gliese 721/HIP 91262/HD 172167`)
- `Celaeno` (별칭: `HD 23288/HIP 17489/16 Tau`)

### 오리온 성운/플레이아데스 성단 내 항성
- `TET1 Ori A` (별칭: `41 Ori A/V1016 Ori/HIP 26220/HD 37020`)
- `TET1 Ori C` (별칭: `41 Ori C`)
- `TET1 Ori D` (별칭: `41 Ori D`)
- `TET1 Ori E`, `TET1 Ori F`, `TET1 Ori G`
- `TET2 Ori A` (별칭: `43 Ori/HIP 26235/HD 37041`)
- `Asterope` (별칭: `21 Tau/Sterope I`)

---

## Stars-fix.sc 항성 수정 (일부 주요 항목)

Stars-fix.sc는 122개 항성의 물리 데이터를 수정합니다. 주요 항목:

- `WR 124` (별칭: `HIP 94289/Merrill's Star`)
- `63 Oph` (별칭: `HD 162978/HIP 87706`)
- `P Cyg` (별칭: `34 Cyg/HIP 100044/HD 193237`)
- `42 Cap` (별칭: `HIP 107095/HD 206301/BY Cap`)
- 대부분 HIP 번호/HD 번호로 등록된 기술적 수정 항목

---

## 외계행성 모항성 (ExoPlanetsSuns.sc) - 2,476개

주요 항목 (IAU 이름 포함):
- `Barnard's Star` (별칭: `Gliese 699/HIP 87937/GJ 699`)
- `AD Leo` (별칭: `Gliese 388/GJ 388`)
- `Ain` (별칭: `EPS Tau/HD 28305/HIP 20889`)
- `Baekdu` (별칭: `8 UMi/HD 133086/HIP 73136`)
- `51 Eri` (별칭: `HD 29391/HIP 21547`)
- `AB Pic` (별칭: `HD 44627/HIP 30034`)

대부분은 `HIP`, `HD`, `Kepler-`, `WASP-`, `HAT-P-`, `CoRoT-`, `TRAPPIST-`, `GJ`, `Gliese` 등의 카탈로그 번호로 등록됩니다.

---

## 주요 외계행성 (ExoPlanets-custom.sc) - 49개 + 외계행성위성 2개

### 주요 외계행성 (IAU 이름 포함)
- `Proxima d` (별칭: `Proxima Cen d/ALF Cen C d`)
- `Proxima b` (별칭: `Proxima Cen b/ALF Cen C b`)
- `Proxima c` (별칭: `Proxima Cen c/ALF Cen C c`)
- `ALF Cen B b`
- `Barnard's Star b` (별칭: `Barnard b/Gliese 699 b/GJ 699 b/HIP 87937 b`)
- `Dimidium` (별칭: `Bellerophon/51 Peg b`) -- ExoPlanets2.sc
- `Osiris` (별칭: `HD 209458 b`)
- `HD 189733 b`
- `Janssen` (별칭: `55 Cnc A e/55 Cnc e`)
- `Galileo` (별칭: `55 Cnc A b/55 Cnc b`)
- `Brahe` (별칭: `55 Cnc A c/55 Cnc c`)
- `Harriot` (별칭: `55 Cnc A f/55 Cnc f`)
- `Lippershey` (별칭: `55 Cnc A d/55 Cnc d`)
- `Enaiposha` (별칭: `Gliese 1214 b/GJ 1214 b`)
- `K2-18 b`
- `SPECULOOS-3 b`
- `Gliese 12 b` (별칭: `GJ 12 b`)
- `Dagon` (별칭: `Fomalhaut b`) -- ExoPlanets.sc
- `Draugr` (별칭: `PSR B1257+12 b`) -- ExoPlanets.sc

### TRAPPIST-1 행성계
- `TRAPPIST-1 b`
- `TRAPPIST-1 c`
- `TRAPPIST-1 d`
- `TRAPPIST-1 e`
- `TRAPPIST-1 f`
- `TRAPPIST-1 g`
- `TRAPPIST-1 h`

### Gliese 581 행성계
- `Gliese 581 e` (별칭: `GJ 581 e`)
- `Gliese 581 b` (별칭: `GJ 581 b`)
- `Gliese 581 c` (별칭: `GJ 581 c`)

### HR 8799 행성계
- `HR 8799 b`, `HR 8799 c`, `HR 8799 d`, `HR 8799 e`

### Kepler 주요 행성
- `Kepler-1 b` (별칭: `TrES-2 b`)
- `Kepler-10 b`
- `Kepler-442 b`
- `Kepler-444 A b` ~ `f`
- `Kepler-1625 b` (외계행성위성 `Kepler-1625 b I` 포함)
- `Kepler-1708 b` (외계행성위성 `Kepler-1708 b I` 포함)

### 기타 주요 외계행성
- `WASP-12 b`
- `HD 106906 b`
- `WD J0914+1914 b`
- `WD 0806-661 B`
- `M51-ULS-1 b`

---

## 외계행성 (ExoPlanets.sc + ExoPlanets2.sc) - 6,011개

대부분 체계적 명명법을 따릅니다:
- `[모항성 이름] b`, `c`, `d`, ...
- 예: `Kepler-186 f`, `WASP-121 b`, `HAT-P-7 b`

일부 IAU 고유이름이 있는 행성 (ExoPlanets.sc에서 발견):
- `Spe` (별칭: `14 And b`)
- `Halla` (별칭: `8 UMi b`)
- `Amateru` (별칭: `EPS Tau b`)
- `Arion` (별칭: `18 Del b`)
- `Arkas` (별칭: `HD 81688 b`)
- `Pirx` (별칭: `BD+14 4559 b`)
- `Finlay` (별칭: `BD-17 63 b`)
- `Fortitudo` (별칭: `KSI Aql b`)
- `Dagon` (별칭: `Fomalhaut b`)
- `Draugr` (별칭: `PSR B1257+12 b`)
- `Ross 128 b`
- `Tau Cet e`, `Tau Cet f`, `Tau Cet g`, `Tau Cet h`
- `Gliese 667 C b` ~ `g`

---

## 소행성 (Asteroids.sc) - 35개

- `Gaspra` (별칭: `(951) Gaspra`)
- `Toutatis` (별칭: `(4179) Toutatis`)
- `Geographos` (별칭: `(1620) Geographos`)
- `1998 KY26`
- `Bacchus` (별칭: `(2063) Bacchus`)
- `Golevka` (별칭: `(6489) Golevka`)
- `Castalia` (별칭: `(4769) Castalia`)
- `Apophis` (별칭: `(99942) Apophis`)
- `Hebe` (별칭: `(6) Hebe`)
- `Iris` (별칭: `(7) Iris`)
- `Flora` (별칭: `(8) Flora`)
- `Metis` (별칭: `(9) Metis`)
- `Psyche` (별칭: `(16) Psyche`)
- `Davida` (별칭: `(511) Davida`)
- `Herculina` (별칭: `(532) Herculina`)
- `Interamnia` (별칭: `(704) Interamnia`)
- `Agamemnon` (별칭: `(911) Agamemnon`)
- `Ganymed` (별칭: `(1036) Ganymed`)
- `Odysseus` (별칭: `(1143) Odysseus`)
- 기타 16개

---

## 카이퍼 벨트 천체 (KuiperBelt.sc) - 72개

### 주요 천체
- `Gonggong` (별칭: `(225088) Gonggong/2007 OR10`)
- `Sedna` (별칭: `(90377) Sedna`)
- `Varuna` (별칭: `(20000) Varuna`)
- `Ixion` (별칭: `(28978) Ixion`)
- `Chariklo` (별칭: `(10199) Chariklo`)
- `Albion` (별칭: `(15760) Albion/1992 QB1`)
- `Dziewanna` (별칭: `(471143) Dziewanna/2010 EK139`)
- `Alicanto` (별칭: `(474640) Alicanto/2004 VN112`)
- `2012 VP113`
- `2014 UZ224` (별칭: `DeeDee`)
- `2018 VG18`

### 켄타우로스 혜성
- `Chiron` (별칭: `(2060) Chiron/95P Chiron`)
- `Echeclus` (별칭: `(60558) Echeclus/174P Echeclus`)

---

## 혜성 (Comets.sc) - 284개

### 유명 혜성
- `Halley` (별칭: `1P (Halley)`)
- `Hale-Bopp` (별칭: `C|1995 O1 (Hale-Bopp)`)
- `Borrelly 3` (별칭: `19P (Borrelly)`)
- `Ikeya-Zhang` (별칭: `153P (Ikeya-Zhang)`)
- `Lovejoy` (별칭: `C|2011 W3 (Lovejoy)`)
- `McNaught` (별칭: `C|2006 P1 (McNaught)`)
- `PANSTARRS` (별칭: `C|2011 L4 (PANSTARRS)`)
- `C|2020 F3 (NEOWISE)` (별칭: `NEOWISE`)
- `ISON` (별칭: `C|2012 S1 (ISON)`)
- 기타 275개 (대부분 `C|` 또는 `P` 접두사의 카탈로그 번호)

> **참고**: SE에서 혜성 이름의 `|`는 `/`와 같은 별칭 구분자가 아니라
> 이름의 일부입니다. `Select "Halley"` 또는 `Select "1P (Halley)"` 형태로 사용합니다.

---

## 백색왜성 (WhiteDwarfs.sc) - 3,648개

대부분 카탈로그 번호로 등록:
- `Luyten 145-141` (별칭: `LP 145-141/GJ 440/Gliese 440/HIP 57367/WD 1142-645`)
- `Wolf 1` (별칭: `Gaia DR3 ...`)
- 나머지: `SDSS J...`, `LAWD ...`, `GD ...`, `EGGR ...`, `PB ...` 등의 체계적 이름

---

## 중성자별/펄서 (NeutronStars.sc) - 2,034개

대부분 `PSR J#####+####` 또는 `PSR B#####+##` 형식:
- `PSR J0030+0451`
- `PSR J0534+2200` (Crab Pulsar에 해당할 수 있음)
- `PSR J0108-1431`
- `PSR B1257+12` (외계행성 보유)
- 기타 ~2,030개

---

## 갈색왜성 (BrownDwarfs.sc) - 4,504개

주요 항목:
- `CFHT-Pl-8`, `Teide 1`, `Teide 2` (플레이아데스 내)
- `Roque 7`, `Roque 15`, `Roque 16` (플레이아데스 내)
- `WISE J...`, `2MASS J...` 형식이 다수
- `Luhman 16A`, `Luhman 16B` (가장 가까운 갈색왜성계)

---

## 블랙홀 (stars/BlackHoles.sc)

### 항성질량 블랙홀 (StarBarycenter) - 43개
- `Sgr A*` (은하 중심 초대질량 블랙홀)
- `HD 226868` (별칭: `Cygnus X-1`)
- `SS 433`
- `GRS 1915+105`
- `GS 2023+338`
- `GRO J1655-40`
- `A 0620-00`
- `XTE J1118+480`
- `LMC X-1`, `LMC X-3`
- `M 33 X-7`
- `QV Tel` (별칭: `HD 167128/HIP 89605/HR 6819`)
- `LB-1 System`
- `Gaia BH1` (별칭: `Gaia DR3 4373465352415301632`)
- `Gaia BH2` (별칭: `Gaia DR3 5870569352746779008`)
- `Gaia BH3` (별칭: `Gaia DR3 4318465066420528000/LS II +14 13`)
- `M51-ULS-1`

### 초대질량 블랙홀 (Star 타입, `*` 접미사) - 129개
초대질량 블랙홀은 은하 이름 뒤에 `*`가 붙는 형식:
- `Powehi` (별칭: `M 87*`)
- `Sgr A*` (은하계 중심)
- `M 31*`, `M 32*`, `M 81*`, `M 82*`
- `3C 273*`
- `TON 618*`
- `IC 1101*`
- `Centaurus A*` (별칭: `NGC 5128*`)
- `Whirlpool*` (별칭: `M 51*/NGC 5194*`)
- `M 105*` (별칭: `NGC 3379*`)
- `M 106*` (별칭: `NGC 4258*`)
- `Holm 15*`
- 기타 ~117개 (NGC, Mrk, PG, SDSS 접두사)

---

## 성운 (Nebulae)

### 주요 성운 - SpriteAstro.sc (15개)
유명한 성운들의 고품질 스프라이트 모델:
- `Pleiades Nebula`
- `IC 2118` (별칭: `Witch Head Nebula`)
- `M 78` (별칭: `NGC 2068`)
- `Orion Nebula` (별칭: `M 42/NGC 1976`)
- `De Mairan's Nebula` (별칭: `M 43/NGC 1982`)
- `Running Man Nebula` (별칭: `Sh2-279/Sharpless 279`)
- `Horsehead Nebula` (별칭: `Barnard 33/LDN 1630`)
- `Flame Nebula` (별칭: `NGC 2024/CED 55P`)
- `NGC 2023` (별칭: `LBN 954`)
- `IC 434`
- `Barnard's Loop` (별칭: `Sh 2-276`)
- `Omega Nebula` (별칭: `Swan Nebula/M 17/NGC 6618`)
- `Homunculus Nebula` (별칭: `Eta Carinae Nebula`)
- `Mystic Mountain Nebula`
- `Keyhole Nebula`

### 주요 성운 - SpriteBambus.sc (95개)
- `NGC 2392` (별칭: `Clownface Nebula/Caldwell 39`)
- `California Nebula` (별칭: `NGC 1499`)
- `IC 1396`
- `Antares Nebula` (별칭: `Rho Ophiuchi Nebula`)
- `Carina Nebula` (별칭: `Grand Nebula/NGC 3372`)
- `Mz 3` (별칭: `Ant Nebula`)
- `Twin Jet Nebula` (별칭: `M2-9/Wings of a Butterfly Nebula`)
- `NGC 6302` (별칭: `Bug Nebula/Butterfly Nebula/Caldwell 69`)
- `Red Rectangle Nebula`
- `Thors Helmet` (별칭: `NGC 2359/IC 468`)
- `Hen 2-104` (별칭: `Southern Crab Nebula`)
- `Calabash Nebula` (별칭: `Rotten Egg Nebula/OH 231.84 +4.22`)
- `North America Nebula` (별칭: `NGC 7000/Caldwell 20`)
- `Rosette Nebula` (별칭: `Caldwell 49`)
- `PacMan Nebula` (별칭: `NGC 281`)
- `Lagoon` (별칭: `M 8/NGC 6523`)
- `Dumbbell` (별칭: `M 27/NGC 6853`)
- `Crab Nebula` (별칭: `M 1/NGC 1952/Taurus A`)
- `Ring Nebula` (별칭: `M 57/NGC 6720`)
- `Hourglass Nebula` (별칭: `ESO 97-1/PN MyCn 18`)
- `Helix Nebula` (별칭: `NGC 7293`)
- `Heart Nebula` (별칭: `IC 1805`)
- `Soul Nebula` (별칭: `IC 1824`)
- `Crescent Nebula`
- `Wizard Nebula` (별칭: `NGC 7380/Sh2-142`)
- `NGC 3132`
- `Ghost of Jupiter` (별칭: `NGC 3242`)
- `Egg Nebula`
- `Stingray Nebula`
- `Boomerang Nebula` (별칭: `Centaurus Bipolar Nebula`)
- `Little Dumbbell Nebula` (별칭: `M 76/NGC 650`)
- `SN 1006`
- `Tycho's Supernova` (별칭: `SN 1572/B Cassiopeiae/3C 10`)
- `Kepler's Supernova` (별칭: `SN 1604`)
- `Cassiopeia A`
- `Retina Nebula` (별칭: `IC 4406`)
- `NGC 6334` (별칭: `Cat's Paw Nebula/Bear Claw Nebula/Gum 64`)
- `Cocoon Nebula` (별칭: `IC 5146/Caldwell 19/Sh 2-125`)
- `Bow-Tie Nebula` (별칭: `NGC 40/Caldwell 2`)
- `NGC 246` (별칭: `Skull Nebula`)
- `Spare-tyre nebula` (별칭: `IC 5148`)
- `NGC 1514`
- `Little Ghost Nebula` (별칭: `NGC 6369`)
- `NGC 3918`
- `NGC 5189`
- 기타 ~50개

### SpriteVoe.sc 성운 (8개)
- `Barnard 68`
- `Christmas Tree Nebula`
- `Cone Nebula`
- `NGC 2264 Nebula`
- `Eagle Nebula` (별칭: `Star Queen Nebula/The Spire/M 16/NGC 6611/IC 4703`)
- `Eagle Pillar`
- `Pillars of Creation`
- `Trifid Nebula` (별칭: `M 20/NGC 6514/Sharpless 30`)

### RaymarchBambus.sc 성운 (20개)
볼류메트릭 레이마칭 렌더 성운:
- `Spirograph Nebula`
- `NGC 6781`
- `NGC 7139`
- `Abell 13`, `Abell 70`, `Abell 30`
- `NGC 6543` (별칭: `Cat's Eye Nebula`)
- `NGC 6537` (별칭: `Red Spider Nebula`)
- `Hen 3-401`
- `Iris Nebula`
- `IC 3568` (별칭: `Lemon Slice Nebula`)
- `Jones-Emberson 1` (별칭: `VV 47`)
- `Owl Nebula` (별칭: `M 97/NGC 3587`)
- `NGC 7009` (별칭: `Saturn Nebula`)
- `Abell 39`
- `Abell 33` (별칭: `PK 238+34.1`)
- `NGC 6826`, `NGC 6891`, `NGC 1535`

### RaymarchPhunnie.sc 성운 (2개)
- `Manatee Nebula` (별칭: `W50/SNR G039.7-02.0`)
- `M 82 Starburst`

### Planetary.sc 행성상 성운 (50개)
- `IC 4776`, `NGC 6620`, `NGC 6445`, `NGC 6644`, `NGC 6629`
- `NGC 6210`, `NGC 6804`, `NGC 6803`, `NGC 6894`, `NGC 6881`
- `NGC 7048`, `NGC 7008`, `IC 2003`, `NGC 2452`, `NGC 3211`
- `IC 2621`, `NGC 5307`, `NGC 5873`, `NGC 6153`
- 기타 ~31개 (Wray, IRAS 접두사 포함)

### SpaceEngine.sc 커스텀 성운 (1개)
- `Skylias Stellar Nursery`

### Extragalactic.sc 외부은하 성운 (1개)
- `NGC 604` (M 33 내)

---

## 은하 (Galaxies)

### 국부은하군 (LocalGroup.sc) - 47개

- `Milky Way`
- `Andromeda` (별칭: `M 31/NGC 224/UGC 454`)
- `Triangulum` (별칭: `M 33/NGC 598/UGC 1117`)
- `Large Magellanic Cloud` (별칭: `LMC/Nubecula Major`)
- `Small Magellanic Cloud` (별칭: `SMC/Nubecula Minor/NGC 292`)
- `Sag dSph`
- `Sculptor dSph` (별칭: `ESO 351-30`)
- `Carina dSph` (별칭: `ESO 206-220`)
- `Sextans dSph` (별칭: `Sextans I`)
- `Ursa Minor Dwarf` (별칭: `UMi dSph`)
- `Draco Dwarf` (별칭: `DDO 208`)
- `Leo I` (별칭: `DDO 74`)
- `Leo II` (별칭: `DDO 93`)
- `CVn I dSph`, `CVn II dSph`
- `Ursa Major I Dwarf` (별칭: `UMa I dSph`)
- `Ursa Major II Dwarf` (별칭: `UMa II dSph`)
- `M 110` (별칭: `NGC 205/UGC 426`)
- `M 32` (별칭: `NGC 221/UGC 452`)
- `NGC 147` (별칭: `UGC 326/DDO 3`)
- `And I` ~ `And VII` (안드로메다 위성은하)
- `Fornax dSph` (별칭: `ESO 356-04`)
- `Wolf-Lundmark-Melotte` (별칭: `WLM/DDO 221`)
- `IC 10` (별칭: `UGC 192`)
- `IC 1613` (별칭: `UGC 668/DDO 8`)
- `Phoenix Dwarf`
- `Leo A` (별칭: `Leo III/DDO 69`)
- `Sextans A` (별칭: `DDO 75`)
- `Sextans B` (별칭: `UGC 5373/DDO 70`)
- `NGC 3109` (별칭: `ESO 499-36`)
- `Sag DIG` (별칭: `ESO 594-4`)
- `Barnard's galaxy` (별칭: `NGC 6822/IC 4895/DDO 209`)
- `Pegasus DIG` (별칭: `DDO 216`)
- `Cetus Dwarf`, `Antlia Dwarf`, `Tucana Dwarf`, `Aquarius Dwarf`

### 주요 은하 (Galaxies.sc) - 25개
- `Tadpole Galaxy` (별칭: `UGC 10214/Arp 188`)
- `Pinwheel` (별칭: `M 101/NGC 5457`)
- `Sombrero` (별칭: `M 104/NGC 4594`)
- `Centaurus A` (별칭: `NGC 5128/Arp 153`)
- `Abell 2261 BCG`
- `M 49` (별칭: `NGC 4472`)
- `M 59` (별칭: `NGC 4621`)
- `M 60` (별칭: `NGC 4649`)
- `M 84` (별칭: `NGC 4374`)
- `M 86` (별칭: `NGC 4406`)
- `M 89` (별칭: `NGC 4552`)
- 기타 Virgo 클러스터 은하

### 추가 은하 (Kexitt.sc) - 89개
- `Whirlpool` (별칭: `M 51/NGC 5194`)
- `NGC 5195` (M 51 동반은하)
- `M 81` (별칭: `NGC 3031`)
- `M 82` (별칭: `NGC 3034`)
- `Hoag's object` (별칭: `PGC 54559`)
- `The Spider Galaxy` (별칭: `UGC 5829`)
- `ESO 510-G13`
- `NGC 2207` / `IC 2163` (충돌 은하)
- `AM 0644`
- `Maffei 1`, `Maffei 2`
- `Dwingeloo 1`, `Dwingeloo 2`
- `UDF 423`
- 기타 ~70개

### 블랙홀 모은하 (BlackholeHosts.sc) - 73개
- `M 87` (별칭: `NGC 4486`)
- `Holmberg 15A` (별칭: `Holm 15`)
- `3C 120` (별칭: `Mrk 1506`)
- `3C 273*` 관련 은하
- `Mrk 335`, `Mrk 421*`, `Mrk 501*` 등 Markarian 은하
- 다수의 PG, SDSS, NGC 은하

### NGC-IC 은하 (NGC-IC.csv) - ~10,843개
CSV 형식으로 NGC/IC 번호가 부여된 은하 카탈로그.
형식: `Name,Type,RA,Dec,Dist,AbsMagn,Radius,Quat.w,Quat.x,Quat.y,Quat.z`

---

## 성단 (Clusters)

### 구상성단 (Globular.sc) - 154개

주요 구상성단:
- `47 Tuc` (별칭: `NGC 104`)
- `OME Cen` (별칭: `NGC 5139`)
- `M 3` (별칭: `NGC 5272`)
- `M 4` (별칭: `NGC 6121`)
- `M 5` (별칭: `NGC 5904`)
- `M 9` (별칭: `NGC 6333`)
- `M 10` (별칭: `NGC 6254`)
- `M 12` (별칭: `NGC 6218`)
- `M 13` (별칭: `NGC 6205`)
- `M 14` (별칭: `NGC 6402`)
- `M 15` (별칭: `NGC 7078`)
- `M 2` (별칭: `NGC 7089`)
- `M 19` (별칭: `NGC 6273`)
- `M 22` (별칭: `NGC 6656`)
- `M 28` (별칭: `NGC 6626`)
- `M 30` (별칭: `NGC 7099`)
- `M 53` (별칭: `NGC 5024`)
- `M 54` (별칭: `NGC 6715`)
- `M 55` (별칭: `NGC 6809`)
- `M 56` (별칭: `NGC 6779`)
- `M 62` (별칭: `NGC 6266`)
- `M 68` (별칭: `NGC 4590`)
- `M 69` (별칭: `NGC 6637`)
- `M 70` (별칭: `NGC 6681`)
- `M 71` (별칭: `NGC 6838`)
- `M 72` (별칭: `NGC 6981`)
- `M 75` (별칭: `NGC 6864`)
- `M 79` (별칭: `NGC 1904`)
- `M 80` (별칭: `NGC 6093`)
- `M 92` (별칭: `NGC 6341`)
- `M 107` (별칭: `NGC 6171`)
- `NGC 2419`
- `NGC 6752`
- `Pal 1` ~ `Pal 15` (Palomar 성단)
- 기타 ~120개

### 산개성단 (Open.sc) - 1,115개

주요 산개성단:
- `Pleiades` (별칭: `M 45/NGC 1432/Melotte 22`)
- `Hyades` (별칭: `Melotte 25`)
- `Praesepe` (별칭: `M 44/NGC 2632`)
- `h Per` (별칭: `NGC 869`)
- `CHI Per` (별칭: `NGC 884`)
- `Southern Pleiades` (별칭: `IC 2602`)
- `Trapezium` (별칭: `TET1 Ori`)
- `M 24` (별칭: `IC 4715/Sagittarius Star Cloud`)
- `Westerlund 1`
- `Westerlund 2`
- `NGC 3603`
- `M 11` (별칭: `NGC 6705`)
- `M 34` (별칭: `NGC 1039`)
- `M 35` (별칭: `NGC 2168`)
- `M 36` (별칭: `NGC 1960`)
- `M 37` (별칭: `NGC 2099`)
- `M 38` (별칭: `NGC 1912`)
- `M 39` (별칭: `NGC 7092`)
- `M 41` (별칭: `NGC 2287`)
- `M 46` (별칭: `NGC 2437`)
- `M 47` (별칭: `NGC 2422`)
- `M 48` (별칭: `NGC 2548`)
- `M 50` (별칭: `NGC 2323`)
- `M 52` (별칭: `NGC 7654`)
- `M 67` (별칭: `NGC 2682/King Cobra Cluster/Golden Eye Cluster`)
- `M 93` (별칭: `NGC 2447`)
- `M 103` (별칭: `NGC 581`)
- `NGC 457`
- `NGC 752`
- `IC 2391`
- `Collinder 285` (Ursa Major Moving Group)
- `Melotte 111` (Coma Star Cluster)
- `NGC 4755` (Jewel Box)
- `Trumpler 14`, `Trumpler 16` (Carina)
- `Sigma Orionis`
- 기타 ~1,080개

### 외부은하 성단 (Extragalactic.sc) - 9개
- `G1` (별칭: `Meyoll II`) -- M 31 내
- `NGC 265` (별칭: `ESO 29-SC14`) -- SMC 내
- `NGC 1755`, `NGC 1783`, `NGC 1978` -- LMC 내
- `NGC 2070` -- LMC 내 (타란튤라 성운)
- `R136` -- LMC 내
- `NGC 2164` -- LMC 내
- `PGC 910901` -- WLM 내

---

## Select 명령 사용 팁

### 기본 사용법
```
Select "Sun"
Select "Earth"
Select "Sirius"
Select "M 31"
Select "Crab Nebula"
```

### 별칭 사용 (어떤 별칭이든 사용 가능)
```
Select "Proxima"           // = Select "Proxima Cen" = Select "ALF Cen C"
Select "Betelgeuse"        // = Select "ALF Ori"
Select "M 42"              // = Select "Orion Nebula" = Select "NGC 1976"
Select "47 Tuc"            // = Select "NGC 104"
```

### 행성/위성 접근 (부모 천체 이름 포함)
```
Select "Earth.Moon"        // 지구의 위성
Select "Jupiter.Io"        // 목성의 위성
Select "Saturn.Titan"      // 토성의 위성
```

### 외계행성
```
Select "Proxima b"         // = Select "Proxima Cen b"
Select "TRAPPIST-1 e"
Select "Dimidium"          // = Select "51 Peg b"
```

### 블랙홀
```
Select "Sgr A*"            // 은하 중심 블랙홀
Select "Cygnus X-1"        // = Select "HD 226868"
Select "Powehi"            // = Select "M 87*"
```

### 참고사항
- SE에서 이름은 대소문자를 구분합니다
- 공백과 특수문자를 포함한 정확한 이름을 사용해야 합니다
- `*` 접미사는 초대질량 블랙홀을 나타냅니다
- `/`로 구분된 이름 중 아무거나 사용 가능합니다
- HIP/HD 번호로도 항성에 접근할 수 있습니다

---

> 이 문서는 `Catalogs.pak`에서 자동 추출되었습니다.
> SpaceEngine 버전에 따라 내용이 다를 수 있습니다.
