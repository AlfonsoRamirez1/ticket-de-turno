$(function () {
  const $form = $("#formTurno");
  const $btn = $form.find("button[type=submit]");
  const $success = $("#successMessage");

  // Función para validar CURP
  function curpDateCheck(curp) {
    const re = /^([A-Z]{4})(\d{2})(\d{2})(\d{2})([HM])(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)([A-Z]{3})([A-Z0-9])(\d)$/i;
    const m = curp.toUpperCase().replace(/\s+/g, "").match(re);
    if (!m) return { ok: false, reason: "Formato CURP inválido (estructura incorrecta)." };

    const yy = parseInt(m[2], 10);
    const mm = parseInt(m[3], 10);
    const dd = parseInt(m[4], 10);
    const year = yy <= 29 ? 2000 + yy : 1900 + yy;
    const date = new Date(year, mm - 1, dd);
    if (date.getFullYear() !== year || date.getMonth() + 1 !== mm || date.getDate() !== dd) {
      return { ok: false, reason: "Fecha inválida en la CURP (YYMMDD incorrecto)." };
    }
    const sexo = m[5].toUpperCase();
    if (!/^[HM]$/.test(sexo)) return { ok: false, reason: "Sexo inválido en CURP (debe ser H o M)." };
    return { ok: true };
  }

  // Función para validar email
  function validateEmailAdvanced(val) {
    if (!val) return { ok: false, reason: "Correo vacío." };
    if ((val.match(/@/g) || []).length !== 1) return { ok: false, reason: "El correo debe contener exactamente un @." };
    const [local, domain] = val.split("@");
    if (!local) return { ok: false, reason: "La parte antes de @ está vacía." };
    if (!domain) return { ok: false, reason: "La parte después de @ está vacía." };
    if (local.length > 64) return { ok: false, reason: "La parte local no puede exceder 64 caracteres." };
    if (/^\./.test(local) || /\.$/.test(local)) return { ok: false, reason: "La parte local no puede empezar/terminar con punto." };
    if (/\.\./.test(local)) return { ok: false, reason: "La parte local no puede tener puntos consecutivos." };
    if (!/[A-Za-zÁÉÍÓÚáéíóúÑñ]/.test(local)) return { ok: false, reason: "La parte local debe contener al menos una letra." };
    if (/\.\./.test(domain)) return { ok: false, reason: "El dominio no puede tener puntos consecutivos." };
    if (domain.split(".").length < 2) return { ok: false, reason: "El dominio debe contener al menos un punto (ej: dominio.com)." };
    const tld = domain.split(".").pop();
    if (!/^[A-Za-z]{2,24}$/.test(tld)) return { ok: false, reason: "TLD inválido (ej: com, mx)." };
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) return { ok: false, reason: "Formato general inválido." };
    return { ok: true };
  }

  // Métodos personalizados para jQuery Validate
  $.validator.addMethod("nameCheck", function (value, element) {
    const v = value.trim();
    if (!v) {
      return false;
    }
    if (/^\d+$/.test(v)) {
      return false;
    }
    if (/^[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ]+$/.test(v)) {
      return false;
    }
    if (/ {2,}/.test(v)) {
      return false;
    }
    if (/^(.)\1{3,}$/.test(v.replace(/\s+/g, ""))) {
      return false;
    }
    if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñüÜ\s'\-]{2,}$/.test(v)) {
      return false;
    }
    return true;
  }, "Formato de nombre inválido");

  $.validator.addMethod("curpCheck", function (value, element) {
    const raw = (value || "").toUpperCase().replace(/\s+/g, "");
    const basicRe = /^[A-Z]{4}\d{6}[HM][A-Z]{2}[A-Z]{3}[A-Z0-9]\d$/i;
    if (!basicRe.test(raw)) {
      return false;
    }
    const res = curpDateCheck(raw);
    if (!res.ok) {
      return false;
    }
    return true;
  }, "CURP inválida");

  $.validator.addMethod("phoneCheck", function (value, element) {
    const digits = value.replace(/\D/g, "");
    if (digits.length < 7 || digits.length > 10) {
      return false;
    }
    if (/^0+$/.test(digits)) {
      return false;
    }
    return true;
  }, "Teléfono inválido");

  $.validator.addMethod("celularCheck", function (value, element) {
    const digits = (value || "").replace(/\D/g, "");
    if (digits.length !== 10) {
      return false;
    }
    if (/^(\d)\1{9}$/.test(digits)) {
      return false;
    }
    return true;
  }, "Celular inválido");

  $.validator.addMethod("emailAdvanced", function (value, element) {
    const res = validateEmailAdvanced(value);
    if (!res.ok) {
      return false;
    }
    return true;
  }, "Correo inválido");

  // Configuración de validación del formulario
  const validator = $form.validate({
    rules: {
      nombreCompleto: { 
        required: true,
        nameCheck: true, 
        minlength: 5 
      },
      curp: { 
        required: true, 
        curpCheck: true 
      },
      nombre: { 
        required: true, 
        nameCheck: true, 
        minlength: 2 
      },
      paterno: { 
        required: true, 
        nameCheck: true, 
        minlength: 2 
      },
      materno: { 
        required: true, 
        nameCheck: true, 
        minlength: 2 
      },
      telefono: { 
        required: true, 
        phoneCheck: true 
      },
      celular: { 
        required: true, 
        celularCheck: true 
      },
      correo: { 
        required: true, 
        emailAdvanced: true 
      },
      nivel: { 
        required: true 
      },
      municipio: { 
        required: true 
      },
      asunto: { 
        required: true 
      }
    },
    messages: {
      nombreCompleto: {
        required: "El nombre completo es requerido",
        minlength: "Mínimo 5 caracteres"
      },
      curp: {
        required: "La CURP es requerida"
      },
      nombre: {
        required: "El nombre es requerido"
      },
      paterno: {
        required: "El apellido paterno es requerido"
      },
      materno: {
        required: "El apellido materno es requerido",
        nameCheck: "Formato de apellido inválido"
      },
      telefono: {
        required: "El teléfono es requerido",
        phoneCheck: "Teléfono inválido (7-10 dígitos)"
      },
      celular: {
        required: "El número celular es requerido",
        celularCheck: "Celular inválido (10 dígitos)"
      },
      correo: {
        required: "El correo electrónico es requerido",
        emailAdvanced: "Correo electrónico inválido"
      },
      nivel: "Por favor seleccione un nivel educativo",
      municipio: "Por favor seleccione un municipio",
      asunto: "Por favor seleccione un asunto"
    },
    errorClass: "error",
    errorElement: "span",
    errorPlacement: function (error, element) {
      error.addClass("error-message");
      error.insertAfter(element);
    },
    highlight: function (element, errorClass) {
      $(element).addClass("error");
    },
    unhighlight: function (element, errorClass) {
      $(element).removeClass("error");
    },
    submitHandler: function (form) {
      $btn.prop("disabled", true).text("Generando...");
      $success.fadeIn(300);
      
      
      setTimeout(function() {
        $success.delay(2000).fadeOut(400, function() {
          $btn.prop("disabled", false).text("Generar Turno");
          form.submit();
        });
      }, 1000);
      
      return false;
    }
  });

  function updateButtonState() {
    const isValid = $form.valid();
    $btn.prop("disabled", !isValid);
  }

  $form.on("input change", "input, select", function() {
    $(this).valid();
    updateButtonState();
  });

  updateButtonState();

  $("#curp").attr("placeholder", "Ej: ABCD010203HDFRRN09");
  $("#correo").attr("placeholder", "ejemplo@dominio.com");
  $("#celular").attr("placeholder", "10 dígitos");
  $("#telefono").attr("placeholder", "7-10 dígitos");
});

