export interface Term {
  et: string;
  en: string;
  description: string;
}

export interface TermCategory {
  key: string;
  terms: Term[];
}

export const terminology: TermCategory[] = [
  {
    key: "ciaTriad",
    terms: [
      {
        et: "Konfidentsiaalsus",
        en: "Confidentiality",
        description: "Teabe kättesaamatus või paljastamatus volitamata isikutele, olematele või protsessidele. Üks kolmest infoturbe põhikomponendist (C-I-A), mis tagab, et ainult volitatud isikud saavad infole juurde pääseda."
      },
      {
        et: "Terviklus",
        en: "Integrity",
        description: "Teabe õigsus ja täielikkus, lubamatute muudatuste puudumine. Üks kolmest infoturbe põhikomponendist (C-I-A), mis hõlmab ka autentsust ja salgamatust - tagab, et info pole volitamata muudetud."
      },
      {
        et: "Käideldavus",
        en: "Availability",
        description: "Teabe omadus olla volitatud olemi nõudel õigel ajal kättesaadav ja kasutuskõlblik. Üks kolmest infoturbe põhikomponendist (C-I-A), mis tagab, et info on vajadusel kättesaadav."
      }
    ]
  },
  {
    key: "riskManagement",
    terms: [
      {
        et: "Risk",
        en: "Risk",
        description: "Ohu võimekus tekitada organisatsioonile kahju. Riski mõõdetakse tavaliselt tõenäosuse ja mõju korrutisena."
      },
      {
        et: "Kahju",
        en: "Loss",
        description: "Soovimatu muutuse mõõt, riskianalüüsi aluskomponent ja esmane infoturbevajadust otsustav tegur."
      },
      {
        et: "Alusohud",
        en: "Base Threats",
        description: "Standardi spetsialisti poolt riskide kaalutlemisel kasutatud ohud; etalonturbe meetmete koostamise alus. Need on eelnevalt määratletud tüüpolud, millega tuleb arvestada."
      },
      {
        et: "Riskihindamine",
        en: "Risk Assessment",
        description: "Protsess, mille käigus identifitseeritakse, analüüsitakse ja hinnatakse riske nende tõenäosuse ja mõju alusel."
      },
      {
        et: "Riskikäsitlus",
        en: "Risk Treatment",
        description: "Protsess riskidega tegelemiseks, sealhulgas riskide vastuvõtmine, vältimine, ülekandmine või vähendamine."
      },
      {
        et: "Riskitaluvus",
        en: "Risk Appetite",
        description: "Organisatsiooni poolt aktsepteeritavate riskide tase, mille ületamisel tuleb rakendada lisameetmeid."
      }
    ]
  },
  {
    key: "isms",
    terms: [
      {
        et: "Infoturbe halduse süsteem",
        en: "Information Security Management System (ISMS)",
        description: "Üldise haldussüsteemi osa infoturbe rajamiseks, elluviimiseks, käigushoiuks, seireks, läbivaatuseks, hoolduseks ja täiustamiseks. Koosneb poliitikaidest, protseduuridest, juhistest ning nendega seotud ressurssidest ja tegevustest."
      },
      {
        et: "Infoturbepoliitika",
        en: "Information Security Policy",
        description: "Kõrgetasemeline dokument, mis määratleb organisatsiooni lähenemise infoturbele, seatud eesmärgid ja üldised põhimõtted."
      },
      {
        et: "Infoturbe eesmärk",
        en: "Information Security Objective",
        description: "Konkreetsed, mõõdetavad eesmärgid, mille saavutamisega infoturvet parendatakse."
      },
      {
        et: "Infoturbe intsident",
        en: "Information Security Incident",
        description: "Soovimatu või ootamatu infoturvasündmus või nende sari, mis võib olulise tõenäosusega rikkuda äritegevust ja ähvardada teabe turvalisust."
      },
      {
        et: "Infoturbeesindaja",
        en: "Information Security Representative",
        description: "Isik, kes vastutab infoturbealaselt koordineerimise ja tegevuse eest organisatsioonis või selle osas."
      }
    ]
  },
  {
    key: "protectionLevels",
    terms: [
      {
        et: "Etalonturve",
        en: "Baseline Protection",
        description: "Standardi hea tava meetmed, mida tuleb rakendada igas organisatsioonis. Põhineb BSI IT-Grundschutz meetodikal ja katab tüüpriskid."
      },
      {
        et: "Kõrge kaitse",
        en: "High Protection",
        description: "Kõrgem kaitstase, mida rakendatakse suurema kaitsetarbega objektidele. Nõuab lisaks etalonturbele täiendavaid meetmeid."
      },
      {
        et: "Kaitsetase",
        en: "Protection Level",
        description: "Määrab, milline kaitse on vajalik konkreetsele äriprotsessile või infovarale. E-ITS defines kolm taset: etalonturve, kõrge kaitse, 标准 baseline."
      },
      {
        et: "Tüüprobjekt",
        en: "Standard Object",
        description: "Infosüsteem, teenus või protsess, mida saab kaitsta etalonturbega. Tüüprobjektid on eelnevalt kategoriseeritud ja neile on määratud standard meetmed."
      },
      {
        et: "Unikaalne lahendus",
        en: "Custom Solution",
        description: "Spetsiifiline lahendus, mis ei kuulu tüüprobjektide hulka ja nõuab individuaalset riskihindamist ja kohandatud turvameetmeid."
      }
    ]
  },
  {
    key: "assetsProcesses",
    terms: [
      {
        et: "Infovara",
        en: "Information Asset",
        description: "Organisatsiooni andmed või teave, mis vajab kaitset. Võib olla digitaalne (failid, andmebaasid) või füüsiline (dokumendid)."
      },
      {
        et: "Äriprotsess",
        en: "Business Process",
        description: "Organisatsiooni tegevuste kogum, mis loob väärtust. Äriprotsessid on seotud organisatsiooni põhieesmärkidega ja vajavad kaitset vastavalt nende tähtsusele."
      },
      {
        et: "Infosüsteem",
        en: "Information System",
        description: "Informatsiooni töötlev ja talletav süsteem koos juurdekuuluvate organisatsiooniliste ressurssidega (inim-, tehnilised ja finantsressursid)."
      },
      {
        et: "Turvaklass",
        en: "Security Class",
        description: "Määratud tase, mis näitab konkreetse infosüsteemi või andmekogu nõutud turvataset (konfidentsiaalsus, terviklus, käideldavus)."
      },
      {
        et: "Andmekogu",
        en: "Data Repository",
        description: "Organisatsiooni poolt hallatav andmete kogum, mis võib olla kasutusel ühe või mitme infosüsteemi poolt."
      }
    ]
  },
  {
    key: "measuresControls",
    terms: [
      {
        et: "Turvameede",
        en: "Security Measure",
        description: "Konkreetsed tegevused või mehhanismid info kaitsmiseks. E-ITS sisaldab ligikaudu 1600 rakendamisele kuuluvat meedet."
      },
      {
        et: "Ennetav meede",
        en: "Preventive Control",
        description: "Meede, mis on loodud tegevust takistama ja turvaintsidentide ennetama enne nende toimumist."
      },
      {
        et: "Avastav meede",
        en: "Detective Control",
        description: "Meede, mis on loodud turvaintsidentide avastamiseks pärast nende toimumist."
      },
      {
        et: "Parandav meede",
        en: "Corrective Control",
        description: "Meede, mis on loodud turvaintsidentide mõju vähendamiseks ja süsteemi normaliseerimiseks."
      },
      {
        et: "Rakenduskava",
        en: "Implementation Plan",
        description: "Dokument, mis kirjeldab turvameetmete rakendamise ajakava, vastutajad ja vajalikud ressursid."
      }
    ]
  },
  {
    key: "audit",
    terms: [
      {
        et: "Auditeerimine",
        en: "Auditing",
        description: "Infoturbe olukorra hindamine organisatsioonis. E-ITS kohustuslik auditeerimine toimub vastavalt auditeerimiseeskirjale."
      },
      {
        et: "Sisemine audit",
        en: "Internal Audit",
        description: "Organisatsiooni enda poolt läbi viidav audit, mis võimaldab ennetlikult avastada puudusi."
      },
      {
        et: "Väline audit",
        en: "External Audit",
        description: "Sõltumatu kolmanda osapoolte poolt läbi viidav audit, mis annab objektiivse hinnangu infoturbele."
      },
      {
        et: "Põhiaudit",
        en: "Main Audit",
        description: "Kõrgeim taseme audit, mis hõlmab kogu organisatsiooni ISMS-i. E-ITS kohustuslastel tuleb läbi viia iga kolme aasta tagant."
      },
      {
        et: "Järelaudit",
        en: "Follow-up Audit",
        description: "Audit, mis kontrollib eelmiste auditileidude parandamist ja soovituste elluviimist."
      },
      {
        et: "Auditeerimiseeskiri",
        en: "Audit Rules",
        description: "Dokument, mis määratleb auditeerimise tingimused, nõuded auditoritele ja auditi läbiviimise protseduurid."
      }
    ]
  },
  {
    key: "roles",
    terms: [
      {
        et: "Tippjuhtkond",
        en: "Top Management",
        description: "Organisatsiooni kõrgeim juhtkond, kes vastutab ISMS-i loomise, rakendamise ja käigushoiu eest ning kinnitab infoturbepoliitika."
      },
      {
        et: "Infoturbe juht",
        en: "Information Security Manager",
        description: "Isik, kes vastutab infoturbe strateegia ja poliitika väljatöötamise ning organisatsiooni infoturbe üldise juhtimise eest."
      },
      {
        et: "Turvakoordinaator",
        en: "Security Coordinator",
        description: "Isik, kes vastutab infoturbe tegevuste koordineerimise eest organisatsioonis ja suhtlemise eest asutuse ja audiitoritega."
      },
      {
        et: "Infosüsteemide spetsialist",
        en: "Information Systems Specialist",
        description: "Spetsialist, kes vastutab ISMS-i rakendamise, tehniliste turvameetmete elluviimise ja infoturbe jälgimise eest."
      },
      {
        et: "IT-haldur",
        en: "IT Administrator",
        description: "Isik, kes vastutab IT-taristu ja süsteemide haldamise, seadistamise ja hoolduse eest, sealhulgas turvaseadete rakendamise eest."
      },
      {
        et: "Andmekaitse spetsialist",
        en: "Data Protection Specialist",
        description: "Isik, kes vastutab isikuandmete töötlemise ja andmekaitse nõuete järgimise eest kooskõlas isikuandmete kaitse seadusega."
      },
      {
        et: "Riskijuht",
        en: "Risk Manager",
        description: "Isik, kes vastutab riskianalüüsi läbiviimise, riskide hindamise ja riskikäsitlusmeetmete väljatöötamise eest."
      },
      {
        et: "Audiitor",
        en: "Auditor",
        description: "Kvalifitseeritud isik, kes viib läbi sõltumatut infoturbe auditeerimist ja annab hinnangu ISMS-i vastavusele."
      }
    ]
  },
  {
    key: "technicalTerms",
    terms: [
      {
        et: "Autentsus",
        en: "Authenticity",
        description: "Omadus, mis kinnitab, et info on pärit deklareeritud allikast ja seda pole muudetud."
      },
      {
        et: "Salgamatus",
        en: "Non-repudiation",
        description: "Võime tõendada, et toiming tehti ja toimingu tegija ei saa seda hiljem eitada."
      },
      {
        et: "Vastutus",
        en: "Accountability",
        description: "Põhimõte, et iga isik on vastutav oma tegevuste eest ja nende tegevuste kohta saab aru anda."
      },
      {
        et: "Kohustuste lahutamine",
        en: "Separation of Duties",
        description: "Vastutuse jaotamine tundliku informatsiooni eest nii, et üksinda tegutsev isik saab rikkuda ainult piiratud osa turvalisust."
      },
      {
        et: "Vähimate õiguste põhimõte",
        en: "Principle of Least Privilege",
        description: "Põhimõte, et kasutajatele antakse minimaalsed õigused, mis on vajalikud nende tööülesannete täitmiseks."
      },
      {
        et: "Kontrollimine",
        en: "Verification",
        description: "Protsess, mille käigus kontrollitakse süsteemi või protsessi vastavust nõutud tingimustele ja standarditele."
      },
      {
        et: "Valideerimine",
        en: "Validation",
        description: "Protsess, mille käigus kinnitatakse, et süsteem või protsess annab soovitud tulemusi."
      },
      {
        et: "Monitooring",
        en: "Monitoring",
        description: "Järjepidev jälgimine ja vaatlemine protsesside, süsteemide või tegevuste kohta, et avastada kõrvalekaldeid."
      },
      {
        et: "Võrgu- ja infosüsteemi turvalisus",
        en: "Network and Information Security",
        description: "Võrkude ja infosüsteemide kaitstus volitamata juurdepääsu, kasutamise, avalikustamise, häirimise, muutmise või hävitamise eest."
      },
      {
        et: "Küberturvalisus",
        en: "Cybersecurity",
        description: "Kõrgetasemeline mõiste, mis hõlmab kõiki tehnoloogiaid, protsesse ja praktikaid, mis kaitsevad võrke, seadmeid, programme ja andmeid rünnakute, kahjustamise või volimatu juurdepääsu eest."
      }
    ]
  },
  {
    key: "standards",
    terms: [
      {
        et: "E-ITS",
        en: "E-ITS",
        description: "Eesti infoturbestandard - eestikeelne ja Eesti õigusruumile vastav infoturbe käsitlemise alus. Kooskõlas rahvusvaheliselt tunnustatud ISO/IEC 27001 standardiga."
      },
      {
        et: "ISKE",
        en: "ISKE",
        description: "Infoturbe klassifikatsioon ja etalonturve - Eesti eelmine infoturbesüsteem, mis kehtis kuni 31.12.2022. Asendatud E-ITS-ga."
      },
      {
        et: "ISO/IEC 27001",
        en: "ISO/IEC 27001",
        description: "Rahvusvaheline infoturbe halduse süsteemide standard. Määrab nõuded ISMS-i loomiseks, rakendamiseks, käigushoiuks ja pidevaks parendamiseks."
      },
      {
        et: "BSI IT-Grundschutz",
        en: "BSI IT-Grundschutz",
        description: "Saksa föderaalse infoturbebüroo (BSI) etalonturbe süsteem, millele E-ITS põhineb. Sisaldab tüüprojekte ja hea tava meetmeid."
      },
      {
        et: "Küberturvalisuse seadus",
        en: "Cybersecurity Act",
        description: "Eesti seadus, mis sätestab küberturvalisuse nõuded ja määrab kindlaks E-ITS kohustuslikud rakendajad."
      },
      {
        et: "EVS-ISO/IEC 27002",
        en: "EVS-ISO/IEC 27002",
        description: "Rahvusvaheline standard, mis annab juhised infoturbe halduse meetmete valimiseks ja rakendamiseks."
      }
    ]
  },
  {
    key: "documentation",
    terms: [
      {
        et: "Nõuded infoturbe halduse süsteemile",
        en: "Requirements for Information Security Management System",
        description: "E-ITS dokument, mis annab üldised juhtnöörid, kuidas organisatsiooni infoturve üles ehitada. Üks kolmest kohustuslikust E-ITS osast."
      },
      {
        et: "Etalonturbe kataloog",
        en: "Baseline Protection Catalogue",
        description: "E-ITS dokument, mis sisaldab nn hea tava meetmeid, mida tuleb rakendada igas organisatsioonis. Sisaldab protsessi- ja tehnoloogiamooduleid."
      },
      {
        et: "Seletav sõnaraamat",
        en: "Explanatory Glossary",
        description: "E-ITS abimaterjal, mille abiga saavad selgemaks E-ITS standardis kasutatud terminid. Põhineb BSI-IT-Grundschutz sõnastikul ja ISO27000 seeria terminite selgitustel."
      },
      {
        et: "Rollisõnastik",
        en: "Role Glossary",
        description: "E-ITS abimaterjal, mis määratleb rollid, mida läheb vaja E-ITS rakendamisel."
      },
      {
        et: "Alusohude kataloog",
        en: "Base Threats Catalogue",
        description: "Dokument, mis sisaldab standardi spetsialisti poolt riskide kaalutlemisel kasutatud оhvusid."
      },
      {
        et: "Riskihaldusjuhend",
        en: "Risk Management Guide",
        description: "E-ITS abimaterjal, mis annab juhised riskihalduse protsessi läbiviimiseks."
      },
      {
        et: "Rakendusjuhend",
        en: "Implementation Guide",
        description: "E-ITS abimaterjal, mis annab soovitused standardi rakendamiseks. Varasemalt kohustuslik, nüüd soovituslik."
      }
    ]
  }
];

export function searchTerms(query: string, language: "et" | "en" = "en"): Term[] {
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return [];

  const results: Term[] = [];
  
  for (const category of terminology) {
    for (const term of category.terms) {
      const searchText = (language === "et" ? term.et : term.en).toLowerCase();
      const descriptionText = term.description.toLowerCase();
      
      if (searchText.includes(normalizedQuery) || descriptionText.includes(normalizedQuery)) {
        results.push(term);
      }
    }
  }
  
  return results;
}