/**
 * CCRCSM — JavaScript principal
 *
 * Principe de conception (TDR §8.3) : amélioration progressive.
 *   Toutes les pages restent lisibles, navigables et soumissibles sans JS.
 *   Ce fichier ajoute des couches de confort : menu mobile, mémoire de langue,
 *   validation client des formulaires, initialisation de la recherche.
 *
 * Sécurité :
 *   - Aucune dépendance externe, aucun eval, aucune manipulation innerHTML avec
 *     des données externes (textContent partout).
 *   - Les données de recherche sont chargées depuis /assets/js/search-index.<locale>.json
 *     qui n'est généré qu'à partir des titres et descriptions propres du site.
 */

(function () {
  "use strict";

  // --------------------------------------------------------------------- //
  // Menu mobile — ouvre/ferme le menu principal avec a11y
  // --------------------------------------------------------------------- //
  function initMobileMenu() {
    const toggle = document.querySelector("[data-menu-toggle]");
    const nav = document.getElementById("primary-nav");
    if (!toggle || !nav) return;

    const openLabel = toggle.querySelector("[data-menu-label-open]");
    const closeLabel = toggle.querySelector("[data-menu-label-close]");

    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      if (openLabel) openLabel.hidden = isOpen;
      if (closeLabel) closeLabel.hidden = !isOpen;
    });

    // Ferme le menu en echap
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        if (openLabel) openLabel.hidden = false;
        if (closeLabel) closeLabel.hidden = true;
        toggle.focus();
      }
    });
  }

  // --------------------------------------------------------------------- //
  // Mémoire de préférence linguistique (TDR §7.1 — confort usager)
  // Stocke dans localStorage la dernière locale utilisée pour guider le
  // prochain accès depuis la racine `/`. Ne modifie jamais le document courant.
  // --------------------------------------------------------------------- //
  function initLangMemory() {
    const locale = document.body.dataset.locale;
    if (!locale) return;
    try {
      localStorage.setItem("ccrcsm:lang", locale);
    } catch {
      // Stockage refusé (mode privé strict) — dégradation silencieuse.
    }
  }

  // --------------------------------------------------------------------- //
  // Validation côté client des formulaires
  // La validation serveur reste l'unique source de vérité (TDR §10.2).
  // --------------------------------------------------------------------- //
  function initForms() {
    const forms = document.querySelectorAll("form[data-validate]");
    forms.forEach((form) => {
      // Renseigne le timestamp d'ouverture pour l'anti-spam serveur
      const ts = form.querySelector('input[name="form_ts"]');
      if (ts) ts.value = String(Date.now());
      form.addEventListener("submit", (e) => {
        const errors = [];
        form.querySelectorAll("[aria-invalid]").forEach((el) =>
          el.setAttribute("aria-invalid", "false")
        );
        form.querySelectorAll("[data-field-error]").forEach((el) => {
          el.textContent = "";
          el.hidden = true;
        });

        form.querySelectorAll("[required]").forEach((el) => {
          if (!el.value || (el.type === "checkbox" && !el.checked)) {
            errors.push({ el, msg: el.dataset.errorRequired || "Champ requis" });
          }
        });

        form.querySelectorAll('input[type="email"]').forEach((el) => {
          if (el.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value)) {
            errors.push({ el, msg: el.dataset.errorEmail || "Email invalide" });
          }
        });

        // Fichier PDF unique, taille 10 Mo max
        form.querySelectorAll('input[type="file"]').forEach((el) => {
          if (el.files && el.files[0]) {
            const f = el.files[0];
            if (f.size > 10 * 1024 * 1024) {
              errors.push({ el, msg: el.dataset.errorFileSize || "Fichier trop volumineux" });
            }
            if (el.accept && !el.accept.split(",").some((t) => f.type === t.trim())) {
              errors.push({ el, msg: el.dataset.errorFileType || "Type non accepté" });
            }
          }
        });

        if (errors.length) {
          e.preventDefault();
          errors.forEach(({ el, msg }) => {
            el.setAttribute("aria-invalid", "true");
            const errId = el.getAttribute("aria-describedby");
            if (errId) {
              const errEl = document.getElementById(errId);
              if (errEl) {
                errEl.textContent = msg;
                errEl.hidden = false;
              }
            }
          });
          errors[0].el.focus();
        }
      });
    });
  }

  // --------------------------------------------------------------------- //
  // Recherche interne côté client (TDR §6.6)
  // L'index est un JSON compact : [{ url, title, description, type, rubrique, date }]
  // La recherche est une correspondance insensible à la casse et aux accents
  // français + tolérance sur les tatweel/diacritiques arabes.
  // --------------------------------------------------------------------- //
  function normalize(str) {
    return String(str || "")
      .toLowerCase()
      .normalize("NFD")
      // Supprime diacritiques latins et arabes (tatweel, fathe, damma, kasra, shadda, sukun…)
      .replace(/[\u0300-\u036f\u0640\u064b-\u0652\u0670]/g, "")
      // Homogénéisation de l'alif arabe (أ إ آ -> ا) et ya (ى -> ي), ta marbuta (ة -> ه)
      .replace(/[\u0622\u0623\u0625]/g, "\u0627")
      .replace(/\u0649/g, "\u064a")
      .replace(/\u0629/g, "\u0647");
  }

  function initSearch() {
    const form = document.querySelector("[data-search-form]");
    const input = document.querySelector("[data-search-input]");
    const results = document.querySelector("[data-search-results]");
    const status = document.querySelector("[data-search-status]");
    const filters = document.querySelectorAll("[data-search-filter]");
    if (!form || !input || !results) return;

    const locale = document.body.dataset.locale || "fr";
    let index = [];
    let activeFilter = "all";

    fetch(`/assets/js/search-index.${locale}.json`, { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        index = Array.isArray(data) ? data : [];
        // Exécute la recherche si un paramètre ?q= est déjà présent
        const params = new URLSearchParams(window.location.search);
        const q = params.get("q");
        if (q) {
          input.value = q;
          search(q);
        }
      })
      .catch(() => { /* indisponibilité silencieuse */ });

    function search(q) {
      const nq = normalize(q).trim();
      if (!nq) {
        results.innerHTML = "";
        if (status) status.textContent = "";
        return;
      }
      const matches = index.filter((it) => {
        if (activeFilter !== "all" && it.type !== activeFilter) return false;
        const hay = normalize([it.title, it.description, it.rubrique].join(" "));
        return hay.includes(nq);
      });
      render(matches, q);
    }

    function render(items, q) {
      results.innerHTML = "";
      if (status) {
        if (items.length === 0) {
          status.textContent = (document.body.dataset.noresults || "Aucun résultat.");
        } else {
          status.textContent = `${items.length} ${document.body.dataset.resultslabel || "résultats"}.`;
        }
      }
      items.forEach((it) => {
        const li = document.createElement("li");
        li.className = "search-result";
        const p = document.createElement("p");
        p.className = "search-result__type";
        p.textContent = it.type || "";
        const h = document.createElement("h3");
        h.className = "search-result__title";
        const a = document.createElement("a");
        a.href = it.url;
        a.textContent = it.title || it.url;
        h.appendChild(a);
        const d = document.createElement("p");
        d.className = "search-result__desc";
        d.textContent = it.description || "";
        li.append(p, h, d);
        results.appendChild(li);
      });
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      search(input.value);
      const url = new URL(window.location.href);
      url.searchParams.set("q", input.value);
      history.replaceState(null, "", url.toString());
    });

    filters.forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.forEach((b) => b.setAttribute("aria-pressed", "false"));
        btn.setAttribute("aria-pressed", "true");
        activeFilter = btn.dataset.searchFilter || "all";
        if (input.value) search(input.value);
      });
    });
  }

  // --------------------------------------------------------------------- //
  // Démarrage
  // --------------------------------------------------------------------- //
  document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initLangMemory();
    initForms();
    initSearch();
  });
})();
