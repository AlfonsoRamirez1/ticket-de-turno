    const $content  = document.getElementById('content');
    const $loader   = document.getElementById('loader');
    const $errorBox = document.getElementById('errorBox');

    function showLoader(show) { $loader.style.display = show ? 'block' : 'none'; }
    function showError(msg) {
      $errorBox.textContent = msg || 'Ocurrió un error al cargar la sección.';
      $errorBox.classList.remove('d-none');
    }
    function hideError() { $errorBox.classList.add('d-none'); }

    // Activa enlace actual
    function setActiveLink(path) {
      document.querySelectorAll('.nav-link').forEach(a => {
        const isActive = a.getAttribute('data-section') === path;
        a.classList.toggle('active', isActive);
        a.setAttribute('aria-current', isActive ? 'page' : '');
      });
    }

    // Carga sección (partial HTML) y actualiza historial
    async function loadSection(path, push = true) {
      try {
        hideError();
        showLoader(true);
        setActiveLink(path);

        const resp = await fetch(path, { headers: { 'X-Requested-With': 'fetch' }});
        if (!resp.ok) {
          throw new Error(`Error ${resp.status}: no se pudo cargar ${path}`);
        }
        const html = await resp.text();
        $content.innerHTML = html;

        if (push) history.pushState({ path }, '', path);
      } catch (err) {
        console.error(err);
        showError(err.message);
      } finally {
        showLoader(false);
      }
    }

    // Delegación de clicks del navbar
    document.addEventListener('click', (ev) => {
      const a = ev.target.closest('a.nav-link, a.navbar-brand');
      if (!a) return;
      const path = a.getAttribute('data-section');
      if (!path) return;

      ev.preventDefault();
      loadSection(path, true);
    });

    // Soporte de atrás/adelante del navegador
    window.addEventListener('popstate', (ev) => {
      const path = ev.state?.path || '/inicio';
      loadSection(path, false);
    });

    (function init() {
      const currentPath = window.location.pathname;
      const allowed = ['/inicio','/crear','/ver','/actualizar','/eliminar'];
      if (allowed.includes(currentPath)) {
        loadSection(currentPath, false);
      } else { 
        loadSection('/inicio', false);
      }
    })();