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
const galleryPrevious = document.querySelector('#gallery-previous');
const galleryNext = document.querySelector('#gallery-next');

function openWorkImage(photo) {
  dialogImage.src = photo.detail_url;
  dialogImage.alt = photo.alt_text || photo.caption || 'Completed electrical work';
  dialogCaption.textContent = photo.caption || '';
  workDialog.showModal();
}

document.querySelectorAll('[data-gallery-detail]').forEach((card) => {
  card.addEventListener('click', (event) => {
    if (!workDialog?.showModal) return;
    event.preventDefault();
    const image = card.querySelector('img');
    openWorkImage({
      detail_url: card.dataset.galleryDetail,
      caption: card.dataset.galleryCaption,
      alt_text: image?.alt || '',
    });
  });
});

function updateGalleryControls() {
  if (!galleryGrid || !galleryPrevious || !galleryNext) return;
  const maximum = galleryGrid.scrollWidth - galleryGrid.clientWidth;
  galleryPrevious.disabled = galleryGrid.scrollLeft < 4;
  galleryNext.disabled = maximum < 4 || galleryGrid.scrollLeft >= maximum - 4;
}

function moveGallery(direction) {
  const card = galleryGrid?.querySelector('.gallery-card');
  if (!card) return;
  const gap = Number.parseFloat(getComputedStyle(galleryGrid).columnGap) || 14;
  galleryGrid.scrollBy({ left: direction * (card.getBoundingClientRect().width + gap), behavior: 'smooth' });
}

galleryPrevious?.addEventListener('click', () => moveGallery(-1));
galleryNext?.addEventListener('click', () => moveGallery(1));
galleryGrid?.addEventListener('scroll', updateGalleryControls, { passive: true });
window.addEventListener('resize', updateGalleryControls);
updateGalleryControls();

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
    const galleryEndpoint = galleryGrid.classList.contains('all-gallery-grid') ? '/api/gallery?all=1' : '/api/gallery';
    const response = await fetch(galleryEndpoint, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Gallery unavailable');
    const photos = await response.json();
    if (!photos.length) return;
    const cards = photos.map((photo) => {
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
    });
    galleryGrid.replaceChildren(...cards);
    requestAnimationFrame(updateGalleryControls);
  } catch (error) {
    console.warn('Gallery could not be loaded.');
  }
}

async function loadReviews() {
  const grid = document.querySelector('#review-grid');
  if (!grid) return;
  try {
    const reviewsEndpoint = grid.dataset.limit === '0' ? '/api/feedback?all=1' : '/api/feedback';
    const response = await fetch(reviewsEndpoint, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Reviews unavailable');
    const reviews = await response.json();
    if (!reviews.length) return;
    const average = reviews.reduce((total, review) => total + review.rating, 0) / reviews.length;
    const summary = document.querySelector('#review-summary');
    if (summary) {
      const roundedBulbs = Math.round(average);
      summary.querySelector('span').textContent = `${'💡'.repeat(roundedBulbs)}${'○'.repeat(5 - roundedBulbs)}`;
      summary.querySelector('strong').textContent = `${average.toFixed(1).replace('.0', '')}/5`;
      summary.setAttribute('aria-label', `${average.toFixed(1)} out of 5 light bulbs`);
    }
    const requestedLimit = Number.parseInt(grid.dataset.limit || '0', 10);
    const visibleReviews = requestedLimit > 0 ? reviews.slice(0, requestedLimit) : reviews;
    grid.replaceChildren(...visibleReviews.map((review) => {
      const card = document.createElement('article');
      card.className = 'review-card';
      const stars = document.createElement('p');
      stars.className = 'review-stars';
      stars.setAttribute('aria-label', `${review.rating} out of 5 light bulbs`);
      stars.textContent = `${'💡'.repeat(review.rating)}${'○'.repeat(5 - review.rating)}`;
      if (review.title) {
        const title = document.createElement('h3');
        title.textContent = review.title;
        card.append(stars, title);
      } else {
        card.append(stars);
      }
      const quote = document.createElement('blockquote');
      quote.textContent = review.comment;
      const source = document.createElement('p');
      source.className = 'review-source-label';
      const date = new Date(review.created_at).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
      });
      source.textContent = `${review.is_test ? 'Test review' : 'Anonymous customer'} · ${date}`;
      card.append(quote, source);
      if (requestedLimit > 0) {
        const more = document.createElement('button');
        more.className = 'review-more';
        more.type = 'button';
        more.textContent = 'Show more';
        more.setAttribute('aria-expanded', 'false');
        const setExpanded = (expanded) => {
          card.classList.toggle('is-expanded', expanded);
          more.textContent = expanded ? 'Show less' : 'Show more';
          more.setAttribute('aria-expanded', String(expanded));
        };
        more.addEventListener('click', () => setExpanded(!card.classList.contains('is-expanded')));
        card.addEventListener('mouseenter', () => setExpanded(true));
        card.addEventListener('mouseleave', () => setExpanded(false));
        card.append(more);
      }
      return card;
    }));
  } catch (error) {
    console.warn('Customer reviews could not be loaded.');
  }
}

loadGallery();
loadReviews();
