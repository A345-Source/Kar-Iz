/* ═══════════════════════════════════════════════════════════════════════════
   KarİZ — main.js — Core Interactivity & Animations
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    // ─── Navbar Scroll Effect ───────────────────────────────────────────────
    const navbar = document.getElementById('navbar');
    if (navbar) {
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.scrollY;
            if (currentScroll > 30) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            lastScroll = currentScroll;
        }, { passive: true });
    }

    // ─── Mobile Hamburger Menu ──────────────────────────────────────────────
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('open');
        });

        // Close menu on link click
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            });
        });

        // Close menu on outside click
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !hamburger.contains(e.target)) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            }
        });
    }

    // ─── Background Particles ───────────────────────────────────────────────
    const bgParticles = document.getElementById('bgParticles');
    if (bgParticles) {
        const particleCount = window.innerWidth < 768 ? 15 : 30;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.width = (Math.random() * 3 + 1) + 'px';
            particle.style.height = particle.style.width;
            particle.style.animationDuration = (Math.random() * 15 + 10) + 's';
            particle.style.animationDelay = (Math.random() * 10) + 's';
            particle.style.opacity = 0;

            // Snow-like particles: slightly blue/white tones
            const colors = [
                'rgba(0, 212, 255, 0.6)',
                'rgba(78, 205, 196, 0.5)',
                'rgba(255, 255, 255, 0.4)',
                'rgba(69, 183, 209, 0.5)',
                'rgba(150, 206, 180, 0.4)'
            ];
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.boxShadow = `0 0 ${Math.random() * 6 + 2}px ${particle.style.background}`;

            bgParticles.appendChild(particle);
        }
    }

    // ─── Intersection Observer: Fade-in on Scroll ───────────────────────────
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeSlideUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements that should animate on scroll
    document.querySelectorAll(
        '.card, .chart-card, .info-card, .havza-kart, .analiz-stat-kart, ' +
        '.trend-ozeti-kart, .sonuc-kart, .gauge-kart, .spi-detay-kart, ' +
        '.meteor-kart, .model-bilgi-kart, .spi-bant-item'
    ).forEach((el, i) => {
        el.style.opacity = '0';
        el.style.animationDelay = `${Math.min(i * 0.05, 0.4)}s`;
        observer.observe(el);
    });

    // ─── Counter Animation ──────────────────────────────────────────────────
    function animateCounter(element, target, duration = 1500) {
        if (!element || isNaN(target)) return;
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (target - start) * eased);
            element.textContent = current.toLocaleString('tr-TR');

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    }

    // Animate stat counters in hero section
    const statGoruntu = document.getElementById('stat-goruntu');
    if (statGoruntu) {
        const targetVal = parseInt(statGoruntu.textContent.replace(/[^\d]/g, ''));
        if (!isNaN(targetVal) && targetVal > 0) {
            const heroObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateCounter(statGoruntu, targetVal, 2000);
                        heroObserver.unobserve(entry.target);
                    }
                });
            });
            heroObserver.observe(statGoruntu);
        }
    }

    // ─── Smooth Page Transitions ────────────────────────────────────────────
    document.querySelectorAll('a[href^="/"]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't interfere with API links or anchor links
            const href = this.getAttribute('href');
            if (href.startsWith('/api/') || href.startsWith('#')) return;

            e.preventDefault();
            document.body.style.opacity = '0.7';
            document.body.style.transition = 'opacity 0.15s ease';

            setTimeout(() => {
                window.location.href = href;
            }, 150);
        });
    });

    // Fade in on page load
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
    requestAnimationFrame(() => {
        document.body.style.opacity = '1';
    });

    // ─── Keyboard Shortcuts ─────────────────────────────────────────────────
    document.addEventListener('keydown', (e) => {
        // Alt + 1-6 for quick navigation
        if (e.altKey && e.key >= '1' && e.key <= '6') {
            const pages = ['/', '/bilimsel-deney', '/harita', '/analiz', '/tahmin', '/uyari'];
            const idx = parseInt(e.key) - 1;
            if (pages[idx]) {
                window.location.href = pages[idx];
            }
        }
    });

    // ─── Tooltip Enhancer for Charts ────────────────────────────────────────
    // Set global Chart.js defaults if available
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
        Chart.defaults.color = '#8B949E';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
        Chart.defaults.plugins.tooltip.backgroundColor = '#1E2D3D';
        Chart.defaults.plugins.tooltip.titleColor = '#00D4FF';
        Chart.defaults.plugins.tooltip.bodyColor = '#ccc';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,212,255,0.3)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.displayColors = true;
        Chart.defaults.plugins.tooltip.boxPadding = 4;
        Chart.defaults.animation = {
            duration: 800,
            easing: 'easeOutQuart'
        };
    }

    // ─── Performance: Reduce animations on low-end devices ──────────────────
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--transition-base', '0ms');
        document.documentElement.style.setProperty('--transition-slow', '0ms');
        document.documentElement.style.setProperty('--transition-spring', '0ms');
    }

    console.log('❄️ KarİZ Web Arayüzü — v1.0.0 yüklendi');
    console.log('🛰️ TÜBİTAK 2204-A — Uydu Tabanlı Kar Örtüsü İzleme');

})();
