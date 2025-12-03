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
    doc.text('Asistencia Vial y Medica en Guatemala', margin, 30);

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
  doc.text('TERMINOS Y CONDICIONES', pageWidth / 2, yPos, { align: 'center' });
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
  addParagraph('Agradecemos la confianza en SegurifAI Guatemala, S.A., para adquirir el Plan de Asistencia para la cuenta en referencia, cuyos terminos y condiciones se presentan a continuacion.');
  yPos += 5;

  addParagraph('SegurifAI Guatemala, S.A., forma parte de un grupo lider en servicios de asistencia que desarrolla principalmente actividades de asistencia vial, medica y servicios relacionados. Tenemos cobertura en toda Guatemala y somos la empresa de referencia en el mercado guatemalteco. Los mas de 50,000 clientes que confian en nosotros lo confirman.');
  yPos += 10;

  addSeparator();

  // Plan-specific benefits
  if (plan.type === 'DRIVE' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('BENEFICIOS DE ASISTENCIA VIAL');
    yPos += 5;

    const vialBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Grua del Vehiculo (Accidente o falla mecanica)', limit: '3 al ano, limite economico $150.00' },
      { name: 'Abasto de Combustible (1 galon)', limit: '3 al ano a elegir, limite economico $150.00' },
      { name: 'Cambio de Neumaticos', limit: '3 al ano a elegir, limite economico $150.00' },
      { name: 'Paso de Corriente', limit: '3 al ano a elegir, limite economico $150.00' },
      { name: 'Emergencia de Cerrajeria', limit: '3 al ano a elegir, limite economico $150.00' },
      { name: 'Servicio de Ambulancia (por accidente)', limit: '1 al ano, limite economico $100.00' },
      { name: 'Servicio de Conductor Profesional', limit: '1 al ano, limite economico $60.00' },
      { name: 'Taxi al Aeropuerto (por viaje al extranjero)', limit: '1 al ano, limite economico $60.00' },
      { name: 'Asistencia Legal Telefonica', limit: '1 al ano, limite economico $200.00' },
      { name: 'Apoyo Economico en Emergencia por Accidente', limit: '1 al ano, limite economico $1,000.00' },
      { name: 'Rayos X', limit: '1 al ano, limite economico $300.00' },
      { name: 'Descuentos en Red de Proveedores', limit: 'Incluido, hasta 20% de descuento' },
      { name: 'Asistente Telefonico (cotizaciones y referencias)', limit: 'Incluido' },
    ];

    vialBenefits.forEach(benefit => {
      checkPageBreak(15);
      addBulletPoint(`${benefit.name}: ${benefit.limit}`);
    });
    yPos += 5;
  }

  if (plan.type === 'HEALTH' || plan.type === 'COMBO') {
    checkPageBreak(50);
    addSubtitle('BENEFICIOS DE ASISTENCIA MEDICA');
    yPos += 5;

    const healthBenefits = [
      { name: 'Seguro Muerte Accidental', limit: 'Q3,000.00' },
      { name: 'Orientacion Medica Telefonica 24/7', limit: 'Incluido' },
      { name: 'Conexion con Especialistas de la Red', limit: 'Incluido' },
      { name: 'Consulta Presencial (Medico General, Ginecologo o Pediatra)', limit: '3 al ano, limite economico $150.00' },
      { name: 'Coordinacion de Medicamentos a Domicilio', limit: 'Incluido' },
      { name: 'Cuidados Post Operatorios de Enfermera', limit: '1 al ano, limite economico $100.00' },
      { name: 'Envio de Articulos de Aseo por Hospitalizacion', limit: '1 al ano, limite economico $100.00' },
      { name: 'Examenes de Laboratorio Basicos', limit: '2 al ano, limite economico $100.00' },
      { name: 'Examenes Especializados (Papanicolau/Mamografia/Antigeno)', limit: '2 al ano, limite economico $100.00' },
      { name: 'Nutricionista Video Consulta (Grupo Familiar)', limit: '4 al ano, limite economico $150.00' },
      { name: 'Psicologia Video Consulta (Nucleo Familiar)', limit: '4 al ano, limite economico $150.00' },
      { name: 'Servicio de Mensajeria por Hospitalizacion', limit: '2 al ano, limite economico $60.00' },
      { name: 'Taxi para Familiar por Hospitalizacion', limit: '2 al ano, limite economico $100.00' },
      { name: 'Traslado en Ambulancia por Accidente', limit: '2 al ano, limite economico $150.00' },
      { name: 'Taxi Post-Alta al Domicilio', limit: '1 al ano, limite economico $100.00' },
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

  addBulletPoint('Limite de Edad de Ingreso: 18 anos a 61 anos inclusive');
  addBulletPoint('Limite de Edad de Terminacion: 70 anos');
  addBulletPoint('Reembolso convencional');
  addBulletPoint('Esta propuesta no contempla la cobertura de uso de motocicleta como medio de transporte.');
  yPos += 10;

  addSeparator();

  // Definition of accident
  checkPageBreak(60);
  addSubtitle('DEFINICION DE ACCIDENTE');
  addParagraph('Se entiende por accidente para los efectos de este seguro, toda lesion corporal sufrida por el Asegurado independientemente de su voluntad y debida a una causa fortuita, momentanea, violenta y externa que le haya producido directamente la muerte, invalidez, perdida de miembros o incapacidad temporal.');
  yPos += 5;

  addSubtitle('SERAN CONSIDERADOS TAMBIEN COMO ACCIDENTES');
  const accidentTypes = [
    'Los causados por explosiones, descargas electricas o atmosfericas.',
    'Las quemaduras causadas por fuego, escapes de vapor imprevistos o contacto accidental con acido y corrosivos.',
    'La asfixia accidental producida por agua, gas, humo o vapores.',
    'Las infecciones respecto a las cuales quede probado que el virus ha penetrado por una lesion producida por un accidente cubierto.',
    'Las mordeduras de animales o picaduras de insectos y sus consecuencias.',
    'Los casos de legitima defensa o tentativas de salvar personas o bienes en peligro.',
    'Los que se produzcan como consecuencia de fenomenos de la naturaleza.',
    'La intoxicacion o envenenamiento por ingestion de sustancias toxicas o alimentos en mal estado.',
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
  addParagraph('El seguro a que se refiere esta Poliza no cubre la muerte, incapacidad, lesiones o cualquier otra perdida causada directa o indirectamente, en todo o en parte por:');
  yPos += 5;

  const exclusions = [
    'Muerte natural.',
    'Lesiones causadas intencionalmente por otra persona cuando el asegurado participe en actos de imprudencia, o participe en actos delictivos o cometiendo un asalto.',
    'Lesion intencionalmente infligida a si mismo, ya sea en estado de cordura o locura.',
    'Guerra (declarada o no), huelgas, motines o rebelion civil, insurreccion, guerra civil, operaciones belicas, o terrorismo nacional e internacional.',
    'Cualquier acto delictuoso en que participe el asegurado directamente con dolo o culpa grave.',
    'La operacion o transporte en ascenso o descenso de cualquier vehiculo aereo si el asegurado es piloto, oficial o miembro de la tripulacion del mismo.',
    'Dolencia corporal o mental, o enfermedad que contribuya total o parcialmente a la muerte.',
    'Veneno, gas o vapores (tragados, administrados, absorbidos o inhalados por accidente o de otra manera voluntaria).',
    'Asfixia por estrangulacion, ya sea voluntaria o involuntariamente.',
    'Hernia, locura.',
    'Cualquier enfermedad o dolencia, prenez o parto.',
    'Accidentes que ocurran mientras el asegurado se encuentre bajo el efecto de estupefacientes, drogas o bebidas alcoholicas.',
    'Mientras participe en reyertas o realice competencias de velocidad en algun vehiculo con ruedas.',
    'Desempenando servicios militares o navales en tiempo de guerra.',
    'Asalto, homicidio o asesinato, o por suicidio o cualquier intento del mismo.',
    'Actos de personas que tomen parte en paros, huelgas o disturbios de caracter obrero, motines, tumultos o alborotos populares.',
  ];

  exclusions.forEach((exclusion, index) => {
    checkPageBreak(20);
    addBulletPoint(`${index + 1}. ${exclusion}`);
  });

  // Procedure in case of accident
  doc.addPage();
  yPos = 20;
  addTitle('AVISO Y PROCEDIMIENTO EN CASO DE ACCIDENTE');
  addParagraph('El asegurado y/o El Contratante deberan dar aviso por escrito a la Compania dentro de los cinco dias siguientes a la fecha del accidente, de cualquier lesion cubierta por la presente Poliza. En caso de muerte accidental, se debera dar aviso inmediato de la misma a la Compania.');
  yPos += 5;
  addParagraph('La Falta de aviso dentro del termino estipulado en esta Poliza no afectara la validez de la reclamacion si se demuestra que no fue posible, dentro de lo razonable, dar tal aviso y que se informo del acontecimiento a la Compania inmediatamente que fue posible.');
  yPos += 10;

  // How to request assistance
  addSeparator();
  addSubtitle('COMO SOLICITAR ASISTENCIA');
  addParagraph('Para solicitar asistencia, utilice cualquiera de los siguientes canales:');
  addBulletPoint('Aplicacion movil SegurifAI - Disponible 24/7');
  addBulletPoint('Linea telefonica de emergencias: 2375-5000');
  addBulletPoint('Portal web: www.segurifai.com.gt');
  yPos += 10;

  // Contact information
  addSeparator();
  addSubtitle('INFORMACION DE CONTACTO');
  addParagraph('SegurifAI Guatemala, S.A.');
  addParagraph('Telefono: 2375-5000');
  addParagraph('Correo: soporte@segurifai.com.gt');
  addParagraph('Sitio web: www.segurifai.com.gt');
  yPos += 10;

  // Footer on last page
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  doc.text('Este documento es generado automaticamente y forma parte de los terminos y condiciones de su plan SegurifAI.', pageWidth / 2, doc.internal.pageSize.getHeight() - 15, { align: 'center' });
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
