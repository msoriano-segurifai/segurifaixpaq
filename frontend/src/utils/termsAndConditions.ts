import jsPDF from 'jspdf';

// Plan types - Updated for SegurifAI Dec 2025
type PlanType = 'RUTA' | 'SALUD' | 'TARJETA' | 'COMBO';

interface PlanInfo {
  name: string;
  type: PlanType;
  price_monthly?: string | number;
  price_yearly?: string | number;
}

// Generate T&Cs PDF for a specific plan
export const generateTermsAndConditionsPDF = (plan: PlanInfo): void => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 20;
  const maxWidth = pageWidth - margin * 2;
  let yPos = 20;

  const addHeader = () => {
    // Logo/Brand
    doc.setFillColor(0, 51, 102); // SegurifAI blue
    doc.rect(0, 0, pageWidth, 35, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.text('SegurifAI', margin, 22);

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Asistencia Vial, Médica y Protección Digital en Guatemala', margin, 30);

    yPos = 50;
  };

  const addTitle = (title: string) => {
    doc.setTextColor(0, 51, 102);
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text(title, margin, yPos);
    yPos += 10;
  };

  const addSubtitle = (subtitle: string) => {
    doc.setTextColor(0, 51, 102);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text(subtitle, margin, yPos);
    yPos += 8;
  };

  const addParagraph = (text: string) => {
    doc.setTextColor(50, 50, 50);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const lines = doc.splitTextToSize(text, maxWidth);
    doc.text(lines, margin, yPos);
    yPos += lines.length * 5 + 3;
  };

  const addBulletPoint = (text: string, indent: number = 0) => {
    doc.setTextColor(50, 50, 50);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const bulletX = margin + indent;
    doc.text('•', bulletX, yPos);
    const lines = doc.splitTextToSize(text, maxWidth - indent - 5);
    doc.text(lines, bulletX + 5, yPos);
    yPos += lines.length * 5 + 2;
  };

  const checkPageBreak = (requiredSpace: number = 30) => {
    if (yPos > doc.internal.pageSize.getHeight() - requiredSpace) {
      doc.addPage();
      yPos = 20;
    }
  };

  const addSeparator = () => {
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    yPos += 8;
  };

  // Start generating PDF
  addHeader();

  // Document title
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('TÉRMINOS Y CONDICIONES', pageWidth / 2, yPos, { align: 'center' });
  yPos += 8;

  doc.setFontSize(12);
  doc.text(`${plan.name}`, pageWidth / 2, yPos, { align: 'center' });
  yPos += 6;

  // Price if available
  if (plan.price_monthly) {
    doc.setFontSize(11);
    doc.setTextColor(0, 128, 0);
    doc.text(`Q${plan.price_monthly}/mes`, pageWidth / 2, yPos, { align: 'center' });
    yPos += 5;
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);
    doc.text('Facturación mensual • Compromiso 12 meses', pageWidth / 2, yPos, { align: 'center' });
    yPos += 5;
  }
  yPos += 10;

  // Date
  doc.setTextColor(50, 50, 50);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  const today = new Date();
  doc.text(`Guatemala, ${today.toLocaleDateString('es-GT', { day: 'numeric', month: 'long', year: 'numeric' })}`, pageWidth - margin, yPos, { align: 'right' });
  yPos += 15;

  // Introduction
  addParagraph('Agradecemos la confianza en SegurifAI Guatemala a través de PAQ Wallet, para adquirir el Plan de Asistencia para la cuenta en referencia, cuyos términos y condiciones se presentan a continuación.');
  yPos += 5;

  addParagraph('SegurifAI Guatemala forma parte de un grupo líder en servicios de asistencia que desarrolla principalmente actividades de asistencia vial, médica y protección digital. Tenemos cobertura en toda Guatemala y somos la empresa de referencia en el mercado guatemalteco.');
  yPos += 10;

  addSeparator();

  // === PROTEGE TU RUTA (Asistencia Vial) ===
  if (plan.type === 'RUTA' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('PROTEGE TU RUTA - SERVICIOS DE ASISTENCIA VIAL');
    addParagraph('Precio: Q39.99/mes (Q479.88/año)');
    yPos += 5;

    const rutaBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Grúa del Vehículo (Accidente o falla mecánica)', limit: '3 al año, límite Q1,170.00' },
      { name: 'Abasto de Combustible (1 galón)', limit: '3 al año, límite combinado Q1,170.00' },
      { name: 'Cambio de Neumáticos', limit: '3 al año, límite combinado Q1,170.00' },
      { name: 'Paso de Corriente', limit: '3 al año, límite combinado Q1,170.00' },
      { name: 'Emergencia de Cerrajería', limit: '3 al año, límite combinado Q1,170.00' },
      { name: 'Servicio de Ambulancia (por accidente)', limit: '1 al año, límite Q780.00' },
      { name: 'Servicio de Conductor Profesional', limit: '1 al año, límite Q470.00 (5hrs anticipación)' },
      { name: 'Taxi al Aeropuerto (por viaje al extranjero)', limit: '1 al año, límite Q470.00' },
      { name: 'Asistencia Legal Telefónica', limit: '1 al año, límite Q1,560.00' },
      { name: 'Apoyo Económico Sala de Emergencia', limit: '1 al año, límite Q7,800.00' },
      { name: 'Rayos X', limit: '1 al año, límite Q2,340.00 (hasta 20% descuento)' },
      { name: 'Descuentos en Red de Proveedores', limit: 'Hasta 20% de descuento' },
      { name: 'Asistente Telefónico Cotización Repuestos', limit: 'Incluido' },
      { name: 'Asistente Telefónico Referencias Médicas', limit: 'Incluido' },
    ];

    rutaBenefits.forEach(benefit => {
      checkPageBreak(15);
      addBulletPoint(`${benefit.name}: ${benefit.limit}`);
    });
    yPos += 5;
  }

  // === PROTEGE TU SALUD (Asistencia Médica) ===
  if (plan.type === 'SALUD' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('PROTEGE TU SALUD - SERVICIOS DE ASISTENCIA MÉDICA');
    addParagraph('Precio: Q34.99/mes (Q419.88/año)');
    yPos += 5;

    const saludBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Orientación Médica Telefónica 24/7', limit: 'Ilimitado' },
      { name: 'Conexión con Especialistas de la Red', limit: 'Ilimitado' },
      { name: 'Coordinación de Medicamentos a Domicilio', limit: 'Ilimitado' },
      { name: 'Consulta Presencial (Médico General, Ginecólogo o Pediatra)', limit: '3 al año, límite Q1,170.00' },
      { name: 'Cuidados Post Operatorios de Enfermera', limit: '1 al año, límite Q780.00' },
      { name: 'Envío de Artículos de Aseo por Hospitalización', limit: '1 al año, límite Q780.00' },
      { name: 'Exámenes Lab: Heces, Orina, Hematología (Grupo Familiar)', limit: '2 al año, límite Q780.00' },
      { name: 'Exámenes: Papanicoláu/Mamografía/Antígeno Prostático', limit: '2 al año, límite Q780.00' },
      { name: 'Nutricionista Video Consulta (Grupo Familiar)', limit: '4 al año, límite Q1,170.00' },
      { name: 'Psicología Video Consulta (Núcleo Familiar)', limit: '4 al año, límite Q1,170.00' },
      { name: 'Servicio de Mensajería por Hospitalización', limit: '2 al año, límite Q470.00' },
      { name: 'Taxi para Familiar por Hospitalización (15km)', limit: '2 al año, límite Q780.00' },
      { name: 'Traslado en Ambulancia por Accidente', limit: '2 al año, límite Q1,170.00' },
      { name: 'Taxi al Domicilio tras Alta (15km)', limit: '1 al año, límite Q780.00' },
    ];

    saludBenefits.forEach(benefit => {
      checkPageBreak(15);
      addBulletPoint(`${benefit.name}: ${benefit.limit}`);
    });
    yPos += 5;
  }

  // === PROTEGE TU TARJETA (Protección Digital) ===
  if (plan.type === 'TARJETA' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('PROTEGE TU TARJETA - PROTECCIÓN CONTRA FRAUDE DIGITAL');
    addParagraph('Precio: Q34.99/mes (Q419.88/año)');
    yPos += 5;

    addParagraph('A) TARJETAS PERDIDAS O ROBADAS:');
    addParagraph('La Aseguradora pagará al Tarjetahabiente por débitos realizados durante el período de cobertura que resulten directamente del uso de alguna Tarjeta Perdida o Robada, por alguna persona no autorizada para: (1) La obtención de dinero o crédito con autorización del Emisor o Cajero Automático, (2) La compra o arrendamiento de bienes o servicios, incluyendo compras por Internet.');
    addParagraph('Los débitos deben haber sido hechos dentro de las 48 horas inmediatamente anteriores a la notificación de la pérdida o robo.');
    yPos += 5;

    addParagraph('B) CLONACIÓN:');
    addBulletPoint('Falsificación y/o Adulteración de la tarjeta');
    addBulletPoint('Falsificación y/o Adulteración de Banda Magnética');
    yPos += 5;

    addParagraph('C) COBERTURA DIGITAL:');
    const digitalCoverage = [
      'Ingeniería Social',
      'Phishing',
      'Robo de Identidad',
      'Suplantación de Identidad (Spoofing)',
      'Vishing (Fraude Telefónico)',
      'Compras Fraudulentas por Internet',
    ];
    digitalCoverage.forEach(coverage => {
      checkPageBreak(15);
      addBulletPoint(coverage);
    });
    yPos += 5;

    addBulletPoint('Seguro Muerte Accidental: Q3,000.00');
    yPos += 10;

    // Exclusions for Card Protection
    checkPageBreak(60);
    addSubtitle('EXCLUSIONES PROTEGE TU TARJETA');
    const cardExclusions = [
      'Fraudes que no se hayan realizado vía online (excepto Robo de Tarjeta física).',
      'Daños consecuenciales como daño moral, pérdida de beneficios, lucro cesante.',
      'Cuando el Asegurado, familiar, amigo o empleado de la Entidad Financiera sea autor o cómplice.',
      'Cuando la tarjeta permanezca bajo custodia de la Entidad Financiera.',
      'Fraudes originados después de 5 días hábiles de entrega del estado de cuenta.',
      'Incumplimiento en pago de obligaciones del Asegurado.',
      'Fraudes en situación de guerra, terrorismo, fenómenos naturales catastróficos.',
      'Pérdidas cubiertas por otro seguro.',
      'Daños en sistemas de la Entidad Financiera.',
      'Ataques de Hackers a la plataforma de la Entidad Financiera.',
      'Usurpación de identidad para adquirir nuevos productos.',
      'Compras fraudulentas por negligencia del Asegurado (compartir credenciales, etc.).',
    ];
    cardExclusions.forEach((exclusion, index) => {
      checkPageBreak(15);
      addBulletPoint(`${index + 1}. ${exclusion}`);
    });
    yPos += 5;
  }

  // General Conditions
  doc.addPage();
  yPos = 20;
  addTitle('CONDICIONES GENERALES');
  yPos += 5;

  addBulletPoint('Límite de Edad de Ingreso: 18 años a 61 años inclusive');
  addBulletPoint('Límite de Edad de Terminación: 70 años');
  addBulletPoint('Reembolso convencional');
  if (plan.type === 'RUTA' || plan.type === 'COMBO') {
    addBulletPoint('Esta propuesta no contempla la cobertura de uso de motocicleta como medio de transporte.');
  }
  yPos += 10;

  // BILLING TERMS SECTION - IMPORTANT
  addSeparator();
  checkPageBreak(80);
  addSubtitle('TÉRMINOS DE FACTURACIÓN Y COMPROMISO');
  yPos += 5;

  // Highlighted billing box
  doc.setFillColor(255, 248, 220); // Light yellow background
  doc.rect(margin, yPos - 2, maxWidth, 45, 'F');
  doc.setDrawColor(200, 150, 0);
  doc.rect(margin, yPos - 2, maxWidth, 45, 'S');
  yPos += 5;

  doc.setTextColor(150, 100, 0);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('IMPORTANTE - LÉASE CUIDADOSAMENTE:', margin + 5, yPos);
  yPos += 8;

  doc.setTextColor(50, 50, 50);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  const billingText1 = 'Este plan tiene un COMPROMISO OBLIGATORIO DE 12 MESES con facturación mensual automática.';
  const lines1 = doc.splitTextToSize(billingText1, maxWidth - 10);
  doc.text(lines1, margin + 5, yPos);
  yPos += lines1.length * 5 + 3;

  doc.setFont('helvetica', 'bold');
  const billingText2 = 'NO ES CANCELABLE antes de completar los 12 meses de compromiso.';
  doc.text(billingText2, margin + 5, yPos);
  yPos += 12;

  doc.setFont('helvetica', 'normal');
  addBulletPoint('Modalidad de pago: Facturación mensual automática durante 12 meses consecutivos.');
  addBulletPoint('Compromiso mínimo: 12 meses desde la fecha de activación del plan.');
  addBulletPoint('Cancelación anticipada: No está permitida la cancelación antes de cumplir los 12 meses de compromiso.');
  addBulletPoint('En caso de impago: El plan se suspenderá temporalmente hasta regularizar el pago. Los meses pendientes deberán ser pagados para completar el ciclo de 12 meses.');
  addBulletPoint('Renovación: Al finalizar los 12 meses, el plan se renovará automáticamente mes a mes, pudiendo cancelar con 30 días de anticipación.');
  addBulletPoint('El costo mensual indicado será debitado automáticamente de su método de pago registrado en PAQ Wallet.');
  yPos += 10;

  addSeparator();

  // Definition of accident (for RUTA and SALUD)
  if (plan.type !== 'TARJETA') {
    checkPageBreak(60);
    addSubtitle('DEFINICIÓN DE ACCIDENTE');
    addParagraph('Se entiende por accidente para los efectos de este seguro, toda lesión corporal sufrida por el Asegurado independientemente de su voluntad y debida a una causa fortuita, momentánea, violenta y externa que le haya producido directamente la muerte, invalidez, pérdida de miembros o incapacidad temporal.');
    yPos += 5;

    addSubtitle('SERÁN CONSIDERADOS TAMBIÉN COMO ACCIDENTES');
    const accidentTypes = [
      'Los causados por explosiones, descargas eléctricas o atmosféricas.',
      'Las quemaduras causadas por fuego, escapes de vapor imprevistos o contacto accidental con ácido y corrosivos.',
      'La asfixia accidental producida por agua, gas, humo o vapores.',
      'Las infecciones respecto a las cuales quede probado que el virus ha penetrado por una lesión producida por un accidente cubierto.',
      'Las mordeduras de animales o picaduras de insectos y sus consecuencias.',
      'Los casos de legítima defensa o tentativas de salvar personas o bienes en peligro.',
      'Los que se produzcan como consecuencia de fenómenos de la naturaleza.',
      'La intoxicación o envenenamiento por ingestión de sustancias tóxicas o alimentos en mal estado.',
    ];
    accidentTypes.forEach(type => {
      checkPageBreak(15);
      addBulletPoint(type);
    });
    yPos += 10;
  }

  // General Exclusions
  doc.addPage();
  yPos = 20;
  addTitle('EXCLUSIONES GENERALES');
  addParagraph('El seguro a que se refiere esta Póliza no cubre la muerte, incapacidad, lesiones o cualquier otra pérdida causada directa o indirectamente, en todo o en parte por:');
  yPos += 5;

  const exclusions = [
    'Muerte natural.',
    'Lesiones causadas intencionalmente por otra persona cuando el asegurado participe en actos de imprudencia, o participe en actos delictivos o cometiendo un asalto.',
    'Lesión intencionalmente infligida a sí mismo, ya sea en estado de cordura o locura.',
    'Guerra (declarada o no), huelgas, motines o rebelión civil, insurrección, guerra civil, operaciones bélicas, o terrorismo nacional e internacional.',
    'Cualquier acto delictuoso en que participe el asegurado directamente con dolo o culpa grave.',
    'La operación o transporte en ascenso o descenso de cualquier vehículo aéreo si el asegurado es piloto, oficial o miembro de la tripulación del mismo.',
    'Dolencia corporal o mental, o enfermedad que contribuya total o parcialmente a la muerte.',
    'Veneno, gas o vapores (tragados, administrados, absorbidos o inhalados por accidente o de otra manera voluntaria).',
    'Asfixia por estrangulación, ya sea voluntaria o involuntariamente.',
    'Hernia, locura.',
    'Cualquier enfermedad o dolencia, preñez o parto.',
    'Accidentes que ocurran mientras el asegurado se encuentre bajo el efecto de estupefacientes, drogas o bebidas alcohólicas.',
    'Mientras participe en reyertas o realice competencias de velocidad en algún vehículo con ruedas.',
    'Desempeñando servicios militares o navales en tiempo de guerra.',
    'Asalto, homicidio o asesinato, o por suicidio o cualquier intento del mismo.',
    'Actos de personas que tomen parte en paros, huelgas o disturbios de carácter obrero, motines, tumultos o alborotos populares.',
  ];

  exclusions.forEach((exclusion, index) => {
    checkPageBreak(20);
    addBulletPoint(`${index + 1}. ${exclusion}`);
  });

  // Procedure in case of accident
  doc.addPage();
  yPos = 20;
  addTitle('AVISO Y PROCEDIMIENTO EN CASO DE SINIESTRO');

  if (plan.type === 'TARJETA') {
    addParagraph('Para reportar un fraude o uso no autorizado de su tarjeta:');
    addBulletPoint('Notifique inmediatamente a SegurifAI a través de la app PAQ Wallet o línea de atención.');
    addBulletPoint('Bloquee su tarjeta con su banco emisor.');
    addBulletPoint('Para tarjetas perdidas o robadas, tiene 48 horas desde el incidente para notificar.');
    addBulletPoint('Proporcione evidencia del fraude (estados de cuenta, capturas de pantalla, etc.).');
    addBulletPoint('En caso de robo, presente denuncia policial (recomendado).');
  } else {
    addParagraph('El asegurado y/o El Contratante deberán dar aviso por escrito a la Compañía dentro de los cinco días siguientes a la fecha del accidente, de cualquier lesión cubierta por la presente Póliza. En caso de muerte accidental, se deberá dar aviso inmediato de la misma a la Compañía.');
    yPos += 5;
    addParagraph('La falta de aviso dentro del término estipulado en esta Póliza no afectará la validez de la reclamación si se demuestra que no fue posible, dentro de lo razonable, dar tal aviso y que se informó del acontecimiento a la Compañía inmediatamente que fue posible.');
  }
  yPos += 10;

  // Contact Information
  addSeparator();
  addSubtitle('CONTACTO');
  addParagraph('Para solicitar asistencia o reportar un siniestro:');
  addBulletPoint('App PAQ Wallet: Sección "Solicitar Asistencia"');
  addBulletPoint('Línea de Atención 24/7: Disponible en la app');
  addBulletPoint('Correo: soporte@segurifai.gt');
  yPos += 10;

  // Footer on last page
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  doc.text('Este documento es generado automáticamente y forma parte de los términos y condiciones de su plan SegurifAI.', pageWidth / 2, doc.internal.pageSize.getHeight() - 20, { align: 'center' });
  doc.text('Proveedor: SegurifAI Guatemala a través de PAQ Wallet', pageWidth / 2, doc.internal.pageSize.getHeight() - 15, { align: 'center' });
  doc.text(`Documento generado el ${today.toLocaleDateString('es-GT')}`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });

  // Save the PDF
  const fileName = `Terminos_y_Condiciones_${plan.name.replace(/\s+/g, '_')}_SegurifAI.pdf`;
  doc.save(fileName);
};

// Determine plan type from name - Updated for SegurifAI Dec 2025
export const getPlanTypeFromName = (planName: string): PlanType => {
  const name = planName.toLowerCase();

  // Check for combo first
  if (name.includes('combo') || name.includes('completo') || name.includes('total')) {
    return 'COMBO';
  }

  // Protege tu Tarjeta / Card protection
  if (name.includes('tarjeta') || name.includes('card') || name.includes('prf') || name.includes('card_insurance')) {
    return 'TARJETA';
  }

  // Protege tu Salud / Health
  if (name.includes('salud') || name.includes('health') || name.includes('medic') || name.includes('médic')) {
    return 'SALUD';
  }

  // Protege tu Ruta / Drive / Roadside (default for vial)
  if (name.includes('ruta') || name.includes('drive') || name.includes('vial') || name.includes('roadside') || name.includes('auto')) {
    return 'RUTA';
  }

  // Default to RUTA if unknown
  return 'RUTA';
};
