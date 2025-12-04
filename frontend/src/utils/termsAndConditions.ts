import jsPDF from 'jspdf';

// Plan types
type PlanType = 'DRIVE' | 'HEALTH' | 'COMBO';

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
    doc.text('Asistencia Vial y Médica en Guatemala', margin, 30);

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
  doc.text(`Plan ${plan.name}`, pageWidth / 2, yPos, { align: 'center' });
  yPos += 15;

  // Date
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  const today = new Date();
  doc.text(`Guatemala, ${today.toLocaleDateString('es-GT', { day: 'numeric', month: 'long', year: 'numeric' })}`, pageWidth - margin, yPos, { align: 'right' });
  yPos += 15;

  // Introduction
  addParagraph('Agradecemos la confianza en SegurifAI Guatemala, S.A., para adquirir el Plan de Asistencia para la cuenta en referencia, cuyos términos y condiciones se presentan a continuación.');
  yPos += 5;

  addParagraph('SegurifAI Guatemala, S.A., forma parte de un grupo líder en servicios de asistencia que desarrolla principalmente actividades de asistencia vial, médica y servicios relacionados. Tenemos cobertura en toda Guatemala y somos la empresa de referencia en el mercado guatemalteco. Los más de 50,000 clientes que confían en nosotros lo confirman.');
  yPos += 10;

  addSeparator();

  // Plan-specific benefits
  if (plan.type === 'DRIVE' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('BENEFICIOS DE ASISTENCIA VIAL');
    yPos += 5;

    const vialBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Grúa del Vehículo (Accidente o falla mecánica)', limit: '3 al año, límite económico Q1,175.00' },
      { name: 'Abasto de Combustible (1 galón)', limit: '3 al año a elegir, límite económico Q1,175.00' },
      { name: 'Cambio de Neumáticos', limit: '3 al año a elegir, límite económico Q1,175.00' },
      { name: 'Paso de Corriente', limit: '3 al año a elegir, límite económico Q1,175.00' },
      { name: 'Emergencia de Cerrajería', limit: '3 al año a elegir, límite económico Q1,175.00' },
      { name: 'Servicio de Ambulancia (por accidente)', limit: '1 al año, límite económico Q785.00' },
      { name: 'Servicio de Conductor Profesional', limit: '1 al año, límite económico Q470.00' },
      { name: 'Taxi al Aeropuerto (por viaje al extranjero)', limit: '1 al año, límite económico Q470.00' },
      { name: 'Asistencia Legal Telefónica', limit: '1 al año, límite económico Q1,570.00' },
      { name: 'Apoyo Económico en Emergencia por Accidente', limit: '1 al año, límite económico Q7,850.00' },
      { name: 'Rayos X', limit: '1 al año, límite económico Q2,355.00' },
      { name: 'Descuentos en Red de Proveedores', limit: 'Incluido, hasta 20% de descuento' },
      { name: 'Asistente Telefónico (cotizaciones y referencias)', limit: 'Incluido' },
    ];

    vialBenefits.forEach(benefit => {
      checkPageBreak(15);
      addBulletPoint(`${benefit.name}: ${benefit.limit}`);
    });
    yPos += 5;
  }

  if (plan.type === 'HEALTH' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('BENEFICIOS DE ASISTENCIA MÉDICA');
    yPos += 5;

    const healthBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Orientación Médica Telefónica 24/7', limit: 'Incluido' },
      { name: 'Conexión con Especialistas de la Red', limit: 'Incluido' },
      { name: 'Consulta Presencial (Médico General, Ginecólogo o Pediatra)', limit: '3 al año, límite económico Q1,175.00' },
      { name: 'Coordinación de Medicamentos a Domicilio', limit: 'Incluido' },
      { name: 'Cuidados Post Operatorios de Enfermera', limit: '1 al año, límite económico Q785.00' },
      { name: 'Envío de Artículos de Aseo por Hospitalización', limit: '1 al año, límite económico Q785.00' },
      { name: 'Exámenes de Laboratorio Básicos', limit: '2 al año, límite económico Q785.00' },
      { name: 'Exámenes Especializados (Papanicoláu/Mamografía/Antígeno)', limit: '2 al año, límite económico Q785.00' },
      { name: 'Nutricionista Video Consulta (Grupo Familiar)', limit: '4 al año, límite económico Q1,175.00' },
      { name: 'Psicología Video Consulta (Núcleo Familiar)', limit: '4 al año, límite económico Q1,175.00' },
      { name: 'Servicio de Mensajería por Hospitalización', limit: '2 al año, límite económico Q470.00' },
      { name: 'Taxi para Familiar por Hospitalización', limit: '2 al año, límite económico Q785.00' },
      { name: 'Traslado en Ambulancia por Accidente', limit: '2 al año, límite económico Q1,175.00' },
      { name: 'Taxi Post-Alta al Domicilio', limit: '1 al año, límite económico Q785.00' },
    ];

    healthBenefits.forEach(benefit => {
      checkPageBreak(15);
      addBulletPoint(`${benefit.name}: ${benefit.limit}`);
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
  addBulletPoint('Esta propuesta no contempla la cobertura de uso de motocicleta como medio de transporte.');
  yPos += 10;

  addSeparator();

  // Definition of accident
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

  // Exclusions
  doc.addPage();
  yPos = 20;
  addTitle('EXCLUSIONES');
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
  addTitle('AVISO Y PROCEDIMIENTO EN CASO DE ACCIDENTE');
  addParagraph('El asegurado y/o El Contratante deberán dar aviso por escrito a la Compañía dentro de los cinco días siguientes a la fecha del accidente, de cualquier lesión cubierta por la presente Póliza. En caso de muerte accidental, se deberá dar aviso inmediato de la misma a la Compañía.');
  yPos += 5;
  addParagraph('La falta de aviso dentro del término estipulado en esta Póliza no afectará la validez de la reclamación si se demuestra que no fue posible, dentro de lo razonable, dar tal aviso y que se informó del acontecimiento a la Compañía inmediatamente que fue posible.');
  yPos += 10;

  // Footer on last page
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  doc.text('Este documento es generado automáticamente y forma parte de los términos y condiciones de su plan SegurifAI.', pageWidth / 2, doc.internal.pageSize.getHeight() - 15, { align: 'center' });
  doc.text(`Documento generado el ${today.toLocaleDateString('es-GT')}`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });

  // Save the PDF
  const fileName = `Terminos_y_Condiciones_${plan.name.replace(/\s+/g, '_')}_SegurifAI.pdf`;
  doc.save(fileName);
};

// Determine plan type from name
export const getPlanTypeFromName = (planName: string): PlanType => {
  const name = planName.toLowerCase();
  if (name.includes('combo') || name.includes('completo')) return 'COMBO';
  if (name.includes('health') || name.includes('salud') || name.includes('medic')) return 'HEALTH';
  return 'DRIVE';
};
