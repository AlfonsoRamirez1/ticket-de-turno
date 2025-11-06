$(function () {
    // --- REFERENCIAS A ELEMENTOS ---
    const $form = $("#formTurno");
    const $btnSubmit = $form.find("button[type=submit]");
    const $municipio = $("#municipio");
    const $oficina = $("#oficina");

    // --- FUNCIONES DE VALIDACIÓN (DE TU validador.js ORIGINAL ) ---

    function curpDateCheck(curp) {
        const re = /^([A-Z]{4})(\d{2})(\d{2})(\d{2})([HM])(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)([A-Z]{3})([A-Z0-9])(\d)$/i;
        const m = (curp || "").toUpperCase().replace(/\s+/g, "").match(re);
        if (!m) return { ok: false, reason: "Formato CURP inválido." };

        const yy = parseInt(m[2], 10);
        const mm = parseInt(m[3], 10);
        const dd = parseInt(m[4], 10);
        const year = yy <= 29 ? 2000 + yy : 1900 + yy;
        const date = new Date(year, mm - 1, dd);
        if (date.getFullYear() !== year || date.getMonth() + 1 !== mm || date.getDate() !== dd) {
            return { ok: false, reason: "Fecha inválida en la CURP." };
        }
        const sexo = m[5].toUpperCase();
        if (!/^[HM]$/.test(sexo)) return { ok: false, reason: "Sexo inválido en CURP." };
        return { ok: true };
    }

    function validateEmailAdvanced(val) {
        if (!val) return { ok: false, reason: "El correo es requerido." };
        if ((val.match(/@/g) || []).length !== 1) return { ok: false, reason: "El correo debe contener un @." };
        const [local, domain] = val.split("@");
        if (!local || !domain) return { ok: false, reason: "Formato inválido (ej: usuario@dominio.com)." };
        if (/\.\./.test(local) || /\.\./.test(domain)) return { ok: false, reason: "No debe tener puntos consecutivos." };
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) return { ok: false, reason: "Formato general inválido." };
        return { ok: true };
    }

    function nameCheck(value) {
        const v = (value || "").trim();
        if (!v) return { ok: false, reason: "Este campo es requerido." };
        if (v.length < 2) return { ok: false, reason: "Mínimo 2 caracteres." };
        if (/^\d+$/.test(v)) return { ok: false, reason: "No puede ser solo números." };
        if (/ {2,}/.test(v)) return { ok: false, reason: "No debe tener espacios consecutivos." };
        if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñüÜ\s'\-]{2,}$/.test(v)) return { ok: false, reason: "Formato de nombre inválido." };
        return { ok: true };
    }

    function phoneCheck(value) { // Para teléfono (opcional)
        const digits = (value || "").replace(/\D/g, "");
        if (digits.length === 0) return { ok: true }; // Es válido si está vacío
        if (digits.length < 7 || digits.length > 10) return { ok: false, reason: "Teléfono inválido (7-10 dígitos)." };
        if (/^0+$/.test(digits)) return { ok: false, reason: "No puede ser solo ceros." };
        return { ok: true };
    }

    function celularCheck(value) { // Para celular (obligatorio)
        const digits = (value || "").replace(/\D/g, "");
        if (digits.length !== 10) return { ok: false, reason: "Celular inválido (10 dígitos)." };
        if (/^(\d)\1{9}$/.test(digits)) return { ok: false, reason: "No pueden ser números repetidos." };
        return { ok: true };
    }

    // --- FUNCIÓN MAESTRA DE VALIDACIÓN ---
    function checkFormValidity() {
        let isFormValid = true;

        // Función para marcar/desmarcar error y mostrar mensaje
        const markError = (selector, validationResult) => {
            const $el = $(selector);
            const $errorSpan = $el.next('.error-message');

            if (validationResult.ok) {
                $el.removeClass('error');
                $errorSpan.text('');
            } else {
                $el.addClass('error');
                $errorSpan.text(validationResult.reason);
                isFormValid = false; // Si CUALQUIER validación falla, el formulario es inválido
            }
        };

        // --- Ejecutar todas las validaciones ---
        markError("#nombreCompleto", nameCheck($("#nombreCompleto").val()));
        markError("#nombre", nameCheck($("#nombre").val()));
        markError("#paterno", nameCheck($("#paterno").val()));
        markError("#materno", nameCheck($("#materno").val()));
        markError("#curp", curpDateCheck($("#curp").val()));
        markError("#telefono", phoneCheck($("#telefono").val()));
        markError("#celular", celularCheck($("#celular").val()));
        markError("#correo", validateEmailAdvanced($("#correo").val()));

        // Validar Selects
        markError("#nivel", $("#nivel").val() ? { ok: true } : { ok: false, reason: "Por favor seleccione un nivel." });
        markError("#municipio", $municipio.val() ? { ok: true } : { ok: false, reason: "Por favor seleccione un municipio." });
        markError("#asunto", $("#asunto").val() ? { ok: true } : { ok: false, reason: "Por favor seleccione un asunto." });

        // Validar Oficina
        const oficinaVal = $oficina.val();
        const oficinaDisabled = $oficina.is(':disabled');
        if (oficinaDisabled) {
             markError("#oficina", { ok: false, reason: "Seleccione un municipio para ver oficinas." });
             isFormValid = false;
        } else if (!oficinaVal) {
             markError("#oficina", { ok: false, reason: "Por favor seleccione una oficina." });
             isFormValid = false;
        } else {
             markError("#oficina", { ok: true });
        }

        // --- Decisión Final ---
        $btnSubmit.prop('disabled', !isFormValid);
    }

    // --- LÓGICA DE CARGA DE OFICINAS ---
    $municipio.on('change', function() {
        const idMunicipio = $(this).val();

        $oficina.prop('disabled', true).html('<option value="">Cargando...</option>');

        if (!idMunicipio) {
            $oficina.html('<option value="">Seleccione un municipio primero</option>');
            checkFormValidity(); // Re-validar (botón se deshabilitará)
            return;
        }

        // Llamamos a la API
        $.getJSON(`/api/oficinas?id_municipio=${idMunicipio}`)
            .done(function(oficinas) {
                if (oficinas.length === 0) {
                    $oficina.html('<option value="">No hay oficinas en este municipio</option>');
                } else {
                    $oficina.prop('disabled', false).html('<option value="">Seleccione una oficina</option>');
                    oficinas.forEach(function(oficina) {
                        $oficina.append($('<option>', {
                            value: oficina.id_oficina,
                            text: oficina.oficina
                        }));
                    });
                }
            })
            .fail(function() {
                $oficina.html('<option value="">Error al cargar oficinas</option>');
            })
            .always(function() {
                // Volvemos a validar DESPUÉS de que la API responda
                checkFormValidity();
            });
    });

    // --- EVENT LISTENER GENERAL ---
    $form.on('input change keyup', 'input, select', function() {
        checkFormValidity();
    });

    // --- ESTADO INICIAL ---
    $("#curp").attr("placeholder", "Ej: ABCD010203HDFRRN09");
    $("#correo").attr("placeholder", "ejemplo@dominio.com");
    $("#celular").attr("placeholder", "10 dígitos (Obligatorio)");
    $("#telefono").attr("placeholder", "7-10 dígitos (Opcional)");

    // Deshabilitar el botón al cargar la página
    checkFormValidity();
});