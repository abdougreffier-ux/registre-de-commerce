/**
 * Glossaire juridique bilingue — référence unique pour l'interface et les contenus.
 * Source de vérité terminologique validée par le secrétariat du Comité (cf. §7.1 TDR).
 * Chaque entrée comporte un identifiant stable et l'équivalent exact dans l'autre langue.
 */
module.exports = [
  {
    id: "registre-du-commerce",
    fr: {
      term: "Registre du commerce",
      definition:
        "Registre tenu par les greffes des tribunaux de commerce, sur lequel sont inscrites les personnes physiques ou morales exerçant une activité commerciale. L'inscription confère la publicité légale des actes relatifs à l'activité.",
    },
    ar: {
      term: "السجل التجاري",
      definition:
        "سجل تمسكه كتابات ضبط المحاكم التجارية، يتم فيه تقييد الأشخاص الطبيعيين والمعنويين الممارسين لنشاط تجاري. يُكسب التقييد الإشهار القانوني للتصرفات المتعلقة بالنشاط.",
    },
  },
  {
    id: "sureté-mobiliere",
    fr: {
      term: "Sûreté mobilière",
      definition:
        "Garantie constituée sur un bien meuble (corporel ou incorporel) en faveur d'un créancier. Comprend le nantissement, le gage et les privilèges, régis en droit mauritanien par la loi n° 2022-011 et les textes d'application.",
    },
    ar: {
      term: "الضمانة المنقولة",
      definition:
        "ضمانة مترتبة على مال منقول (مادي أو معنوي) لفائدة الدائن. تشمل الرهن الحيازي والرهن الرسمي والامتيازات، وتُنظّم في القانون الموريتاني بالقانون رقم 011-2022 والنصوص التطبيقية.",
    },
  },
  {
    id: "nantissement",
    fr: {
      term: "Nantissement",
      definition:
        "Affectation d'un bien meuble incorporel (fonds de commerce, créances, parts sociales) en garantie d'une créance, sans dépossession du débiteur.",
    },
    ar: {
      term: "الرهن الحيازي على المنقولات المعنوية",
      definition:
        "تخصيص مال منقول معنوي (أصل تجاري، ديون، حصص اجتماعية) ضمانًا لدين، دون نقل حيازته من المدين.",
    },
  },
  {
    id: "gage",
    fr: {
      term: "Gage",
      definition:
        "Contrat par lequel un débiteur remet à un créancier un bien meuble corporel en garantie d'une dette. Peut s'exercer avec ou sans dépossession selon la nature du bien.",
    },
    ar: {
      term: "الرهن الحيازي",
      definition:
        "عقد يقدم بموجبه المدين إلى الدائن مالًا منقولًا ماديًا ضمانًا لدين. يُباشر مع نقل الحيازة أو بدونه بحسب طبيعة المال.",
    },
  },
  {
    id: "immatriculation",
    fr: {
      term: "Immatriculation",
      definition:
        "Inscription initiale d'un commerçant, d'une société ou d'une personne morale au registre du commerce, conférant la personnalité juridique commerciale et rendant les actes opposables aux tiers.",
    },
    ar: {
      term: "التقييد الأصلي",
      definition:
        "التسجيل الأولي لتاجر أو شركة أو شخص معنوي في السجل التجاري، ويكسب الشخصية القانونية التجارية ويجعل التصرفات نافذة في مواجهة الغير.",
    },
  },
  {
    id: "radiation",
    fr: {
      term: "Radiation",
      definition:
        "Suppression de l'inscription d'une personne ou d'un acte du registre du commerce, à la suite d'une cessation d'activité, d'une décision judiciaire ou d'une mainlevée.",
    },
    ar: {
      term: "الشطب",
      definition:
        "حذف تقييد شخص أو تصرف من السجل التجاري، على إثر توقف النشاط أو صدور حكم قضائي أو رفع الضمانة.",
    },
  },
  {
    id: "privilege",
    fr: {
      term: "Privilège",
      definition:
        "Droit conféré par la loi à un créancier d'être payé, à raison de la qualité de sa créance, avant les autres créanciers, y compris hypothécaires.",
    },
    ar: {
      term: "الامتياز",
      definition:
        "حق يُكسبه القانون للدائن في استيفاء دينه، بسبب طبيعة هذا الدين، قبل سائر الدائنين بمن فيهم أصحاب الرهون الرسمية.",
    },
  },
  {
    id: "mainlevee",
    fr: {
      term: "Mainlevée",
      definition:
        "Acte juridique par lequel une sûreté est levée, libérant le bien grevé et entraînant la radiation de l'inscription correspondante.",
    },
    ar: {
      term: "رفع الضمانة",
      definition:
        "تصرف قانوني تُرفع بموجبه الضمانة، فيتحرر المال المثقل ويُشطب التقييد المتعلق به.",
    },
  },
  {
    id: "avis-du-comite",
    fr: {
      term: "Avis du Comité",
      definition:
        "Position formelle prise par le Comité sur une question soumise par les personnes chargées de la tenue du registre, publiée sur le site officiel pour information des usagers.",
    },
    ar: {
      term: "رأي اللجنة",
      definition:
        "موقف رسمي تتخذه اللجنة في مسألة محالة إليها من الأشخاص المكلفين بمسك السجل، يُنشر على الموقع الرسمي لعلم المرتفقين.",
    },
  },
];
