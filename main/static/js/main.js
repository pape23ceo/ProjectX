const input = document.getElementById('search-input');
const ghostInput = document.getElementById('ghost-input');
const suggestionsBox = document.getElementById('suggestions');
const cityList = document.getElementById('city-list');
const emptyState = document.getElementById('empty-state');
const clearBtn = document.getElementById('clear-btn');
let pincodeDebounce;
let lastNameResults = [];

const STORAGE_KEY = 'recentCities';
const MAX_RECENTS = 5;

function getRecents() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch (e) {
        return [];
    }
}

function saveRecent(place) {
    let recents = getRecents();
    recents = recents.filter(p => !(p.latitude === place.latitude && p.longitude === place.longitude));
    recents.unshift(place);
    recents = recents.slice(0, MAX_RECENTS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(recents));
}

function removeRecent(latitude, longitude) {
    const recents = getRecents().filter(p => !(p.latitude === latitude && p.longitude === longitude));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(recents));
}

input.addEventListener('input', () => {
    clearBtn.classList.toggle('hidden', input.value.length === 0);
    ghostInput.value = '';

    if (input.value.length === 0) {
        suggestionsBox.classList.add('hidden');
        clearTimeout(pincodeDebounce);
        return;
    }

    const looksLikePincode = /^\d{4,6}$/.test(input.value.trim());
    clearTimeout(pincodeDebounce);
    if (looksLikePincode) {
        pincodeDebounce = setTimeout(() => lookupPincode(input.value.trim()), 150);
    }
});

input.addEventListener('keydown', (e) => {
    const hasGhost = ghostInput.value && ghostInput.value.length > input.value.length;
    const atEnd = input.selectionStart === input.value.length;
    if (hasGhost && atEnd && (e.key === 'Tab' || e.key === 'ArrowRight')) {
        e.preventDefault();
        input.value = ghostInput.value;
        ghostInput.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        htmx.trigger(input, 'search');
    }
});

function updateGhost(candidateName) {
    if (!candidateName || !input.value) {
        ghostInput.value = '';
        return;
    }
    if (candidateName.toLowerCase().startsWith(input.value.toLowerCase())) {
        ghostInput.value = input.value + candidateName.slice(input.value.length);
    } else {
        ghostInput.value = '';
    }
}

async function lookupPincode(code) {
    const candidates = code.length === 6 ? ['in', 'sg']
        : code.length === 5 ? ['us', 'de', 'fr', 'es', 'it']
            : ['au', 'nl', 'be', 'ch', 'at'];

    const attempts = candidates.map(cc =>
        fetch(`https://api.zippopotam.us/${cc}/${code}`).then(r => r.ok ? r.json() : null).catch(() => null)
    );
    const results = await Promise.all(attempts);
    const data = results.find(r => r && r.places && r.places.length);

    if (!/^\d{4,6}$/.test(input.value.trim())) return;

    if (!data) {
        suggestionsBox.classList.add('hidden');
        suggestionsBox.innerHTML = '';
        return;
    }

    const places = data.places.map(p => ({
        name: p['place name'],
        admin1: p.state || '',
        country: data.country,
        latitude: parseFloat(p.latitude),
        longitude: parseFloat(p.longitude)
    }));

    renderSuggestions(places);
}

function clearSearch() {
    input.value = '';
    ghostInput.value = '';
    clearBtn.classList.add('hidden');
    suggestionsBox.classList.add('hidden');
    input.focus();
}

document.body.addEventListener('htmx:afterRequest', async (evt) => {
    if (evt.target !== input) return;
    if (!evt.detail.successful) return;
    if (/^\d{4,6}$/.test(input.value.trim())) return;

    let data;
    try {
        data = JSON.parse(evt.detail.xhr.responseText);
    } catch (e) {
        return;
    }

    const results = (data.features || []).map(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        return {
            name: props.name || '',
            admin1: props.state || props.county || '',
            country: props.country || '',
            latitude: coords[1],
            longitude: coords[0]
        };
    });

    lastNameResults = results;
    updateGhost(results[0] && results[0].name);
    renderSuggestions(results);
});

function renderSuggestions(results) {
    if (results.length === 0) {
        suggestionsBox.classList.add('hidden');
        suggestionsBox.innerHTML = '';
        return;
    }

    suggestionsBox.innerHTML = results.map((r, i) => `
    <button
      type="button"
      class="suggestion-item w-full text-left px-4 py-3.5 flex flex-col min-h-[44px] justify-center ${i !== results.length - 1 ? 'border-b border-white/5' : ''}"
      onclick='selectCity(${JSON.stringify(r).replace(/'/g, "&apos;")})'>
      <span class="text-base text-gray-100">${r.name}</span>
      <span class="text-xs text-gray-500 truncate max-w-full">${[r.admin1, r.country].filter(Boolean).join(', ')}</span>
    </button>
  `).join('');
    suggestionsBox.classList.remove('hidden');
    suggestionsBox.classList.add('fade-in');
}

function selectCity(place) {
    suggestionsBox.classList.add('hidden');
    input.value = '';
    ghostInput.value = '';
    clearBtn.classList.add('hidden');

    saveRecent(place);
    goToWeatherDetails(place.latitude, place.longitude);
}

function loadRecent(place) {
    const cardHtml = renderCard(place);
    cityList.insertAdjacentHTML('beforeend', cardHtml);
    emptyState.classList.add('hidden');
}

function removeCity(latitude, longitude, cardEl) {
    removeRecent(latitude, longitude);
    cardEl.remove();
    if (cityList.children.length === 0) emptyState.classList.remove('hidden');
}

function goToWeatherDetails(lat, lon) {
    window.location.href = `{% url 'weather_info' %}?coordinates=${lat},${lon}`;
}

window.addEventListener('DOMContentLoaded', () => {
    const recents = getRecents();
    recents.forEach(loadRecent);
});

function renderCard(place) {
    const subtitle = [place.admin1, place.country].filter(Boolean).join(', ');
    return `
    <div onclick="goToWeatherDetails(${place.latitude}, ${place.longitude})" 
         class="card-enter group relative rounded-2xl bg-gradient-to-br from-[#2a2a2c] to-[#1c1c1e] active:scale-[0.98] transition-all px-5 py-4 flex flex-col gap-0.5 shadow-md border border-white/[0.03] cursor-pointer min-h-[72px] justify-center"
         data-lat="${place.latitude}" data-lon="${place.longitude}">
      
      <!-- Safe Tap Area Delete Button: Always visible on mobile, group-hover on desktop -->
      <button
        type="button"
        onclick="event.stopPropagation(); removeCity(${place.latitude}, ${place.longitude}, this.closest('[data-lat]'))"
        class="absolute top-1/2 -translate-y-1/2 right-4 w-9 h-9 rounded-full bg-white/5 md:bg-black/20 text-white/70 active:bg-white/10 md:opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center z-10">
        <span class="text-base leading-none">✕</span>
      </button>

      <div class="flex items-center gap-1.5 pr-8">
        <span class="text-base sm:text-lg font-medium tracking-tight truncate">${place.name}</span>
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-500 shrink-0" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/>
        </svg>
      </div>
      <span class="text-xs sm:text-sm text-gray-500 truncate pr-8">${subtitle}</span>
    </div>
  `;
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('#search-input') && !e.target.closest('#suggestions')) {
        suggestionsBox.classList.add('hidden');
    }
});