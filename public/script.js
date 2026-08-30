const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('#site-nav');

menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!open));
  nav.classList.toggle('open', !open);
});

nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
  nav.classList.remove('open');
  menuButton?.setAttribute('aria-expanded', 'false');
}));

const year = document.querySelector('#year');
if (year) year.textContent = new Date().getFullYear();

const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
  if (entry.isIntersecting) {
    entry.target.classList.add('visible');
    observer.unobserve(entry.target);
  }
}), { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));

const galleryGrid = document.querySelector('#gallery-grid');
const workDialog = document.querySelector('#work-dialog');
const dialogImage = document.querySelector('#work-dialog-image');
const dialogCaption = document.querySelector('#work-dialog-caption');

function openWorkImage(photo) {
  dialogImage.src = photo.detail_url;
  dialogImage.alt = photo.alt_text || photo.caption || 'Completed electrical work';
  dialogCaption.textContent = photo.caption || '';
  workDialog.showModal();
}

workDialog?.querySelector('.dialog-close')?.addEventListener('click', () => workDialog.close());
workDialog?.addEventListener('click', (event) => {
  if (event.target === workDialog) workDialog.close();
});
workDialog?.addEventListener('close', () => {
  dialogImage.removeAttribute('src');
  dialogImage.alt = '';
});

async function loadGallery() {
  if (!galleryGrid) return;
  try {
    const response = await fetch('/api/gallery', { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Gallery unavailable');
    const photos = await response.json();
    if (!photos.length) return;
    galleryGrid.replaceChildren(...photos.map((photo) => {
      const button = document.createElement('button');
      button.className = 'gallery-card';
      button.type = 'button';
      button.addEventListener('click', () => openWorkImage(photo));
      const image = document.createElement('img');
      image.src = photo.thumbnail_url;
      image.alt = photo.alt_text || photo.caption || 'Completed electrical work';
      image.loading = 'lazy';
      image.decoding = 'async';
      image.width = 640;
      image.height = 480;
      const caption = document.createElement('span');
      caption.textContent = photo.caption || 'View project';
      button.append(image, caption);
      return button;
    }));
  } catch (error) {
    console.warn('Gallery could not be loaded.');
  }
}

async function loadFeedback() {
  const grid = document.querySelector('#feedback-grid');
  if (!grid) return;
  try {
    const response = await fetch('/api/feedback', { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Feedback unavailable');
    const entries = await response.json();
    if (!entries.length) return;
    grid.replaceChildren(...entries.map((entry) => {
      const article = document.createElement('article');
      article.className = 'feedback-card';
      const stars = document.createElement('p');
      stars.className = 'feedback-stars';
      stars.setAttribute('aria-label', `${entry.rating} out of 5 stars`);
      stars.textContent = `${'★'.repeat(entry.rating)}${'☆'.repeat(5 - entry.rating)}`;
      const quote = document.createElement('blockquote');
      quote.textContent = entry.comment;
      const label = document.createElement('p');
      label.className = 'feedback-label';
      label.textContent = 'Anonymous customer';
      article.append(stars, quote, label);
      return article;
    }));
  } catch (error) {
    console.warn('Feedback could not be loaded.');
  }
}

loadGallery();
loadFeedback();
