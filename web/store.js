let products = [
  { id: "camera-x2", name: "Summit Mirrorless Camera X2", category: "Camera gear", price: 849, rating: 4.9, reviews: 284, emoji: "📷", image: "photo-1516035069371-29a1b244cc32", art: "art-camera", label: "BESTSELLER", colors: ["#dce6d8", "#a9b9a2"], description: "A brilliant little camera for big days out. Weather-sealed, travel-ready, and just as happy capturing a quiet morning as a summit sunrise.", details: ["26 MP back-illuminated sensor", "Weather-sealed magnesium body", "Two-day battery life"] },
  { id: "trail-pack-28", name: "Trailblazer 28L Daypack", category: "Outdoor", price: 94, rating: 4.8, reviews: 192, emoji: "🎒", image: "photo-1553062407-98eeb64c6a62", art: "art-pack", label: "CUSTOMER FAVORITE", colors: ["#e5e8d8", "#bdc7a8"], description: "The just-right daypack: enough room for a camera, lunch, and an extra layer, without making the walk feel like work.", details: ["28-liter everyday capacity", "Padded camera-friendly sleeve", "Recycled, water-resistant fabric"] },
  { id: "prime-lens-50", name: "Peak 50mm Prime Lens", category: "Camera gear", price: 329, rating: 4.9, reviews: 156, emoji: "🔭", image: "photo-1502920917128-1aa500764cbd", art: "art-lens", label: "PAIRING PICK", colors: ["#e8e5d9", "#c7c2b4"], description: "A lovely, bright prime lens for portraits and low-light moments. Small enough to stay on the camera all weekend.", details: ["Bright f/1.8 aperture", "Quiet, quick autofocus", "Compact metal construction"] },
  { id: "camera-sling", name: "Field Notes Camera Sling", category: "Accessories", price: 68, rating: 4.7, reviews: 98, emoji: "👜", image: "photo-1622560480654-d96214fdc887", art: "art-sling", label: "TRAVEL PICK", colors: ["#e8dfd3", "#c9b59f"], description: "Keep your everyday camera close, comfortable, and ready for the unexpected turn down a side street.", details: ["Adjustable padded strap", "Soft-lined camera compartment", "Weather-resistant canvas"] },
  { id: "trail-shell", name: "Ridgeline Waterproof Trail Shell", category: "Outdoor", price: 129, rating: 4.8, reviews: 143, emoji: "🧥", image: "photo-1551028719-00167b16eac5", art: "art-pack", label: "NEW SEASON", colors: ["#dce6d8", "#a9b9a2"], description: "A lightweight shell that earns its place in the pack. Pull it on when the weather changes and keep moving.", details: ["Packable three-layer fabric", "Adjustable hood and cuffs", "Sealed seams for wet weather"] },
  { id: "summit-boots", name: "Summit Grip Hiking Boots", category: "Outdoor", price: 159, rating: 4.8, reviews: 211, emoji: "🥾", image: "photo-1542291026-7eec264c27ff", art: "art-sling", label: "TRAIL TESTED", colors: ["#e8dfd3", "#c9b59f"], description: "Comfortable support for the long way round, with dependable grip on rocky paths and muddy shortcuts.", details: ["All-terrain rubber outsole", "Cushioned ankle support", "Water-resistant nubuck leather"] },
  { id: "carbon-tripod", name: "Waypoint Carbon Travel Tripod", category: "Camera gear", price: 119, rating: 4.7, reviews: 87, emoji: "📸", image: "photo-1500530855697-b586d89ba3ee", art: "art-lens", label: "LIGHTWEIGHT", colors: ["#e8e5d9", "#c7c2b4"], description: "A steady place to set the camera for a long exposure, a group photo, or a well-earned coffee stop.", details: ["Lightweight carbon-fiber legs", "Quick-lock height adjustment", "Folds down for easy travel"] },
  { id: "field-drive", name: "Fieldwork 1TB Portable SSD", category: "Accessories", price: 109, rating: 4.8, reviews: 76, emoji: "💾", image: "photo-1597872200969-2b65d56bd16b", art: "art-camera", label: "FIELD ESSENTIAL", colors: ["#dce6d8", "#a9b9a2"], description: "A pocket-sized backup for the photos and videos you would rather not leave behind.", details: ["1TB solid-state storage", "Rugged, travel-friendly case", "Fast USB-C transfer"] },
  { id: "ridge-poles", name: "Ridgeway Carbon Trekking Poles", category: "Outdoor", price: 79, rating: 4.7, reviews: 64, emoji: "🥾", image: "photo-1551632811-561732d1e306", art: "art-pack", label: "TRAIL ESSENTIAL", colors: ["#e5e8d8", "#bdc7a8"], description: "Light, adjustable poles for steady steps on steep climbs and long descents.", details: ["Lightweight carbon construction", "Quick-adjust locking system", "Comfort-grip cork handles"] },
  { id: "merino-socks", name: "Switchback Merino Trail Socks", category: "Outdoor", price: 24, rating: 4.8, reviews: 138, emoji: "🧦", image: "photo-1551632811-561732d1e306", art: "art-sling", label: "SMALL COMFORT", colors: ["#e8dfd3", "#c9b59f"], description: "A soft merino blend that keeps long trail days comfortable, mile after mile.", details: ["Merino wool blend", "Cushioned heel and toe", "Breathable arch support"] },
  { id: "packing-cubes", name: "Wanderlight Packing Cube Set", category: "Accessories", price: 38, rating: 4.6, reviews: 52, emoji: "🧳", image: "photo-1622560480654-d96214fdc887", art: "art-camera", label: "PACK SMARTER", colors: ["#dce6d8", "#a9b9a2"], description: "Keep spare layers and weekend essentials neat between the trailhead and the guesthouse.", details: ["Three sizes in one set", "Lightweight recycled nylon", "Two-way compression zips"] },
  { id: "alpine-hammock", name: "Alpine Drift Camp Hammock", category: "Outdoor", price: 89, rating: 4.9, reviews: 91, emoji: "🏕️", image: "photo-1478131143081-80f7f84ca84d", art: "art-pack", label: "SLOW DOWN", colors: ["#dce6d8", "#a9b9a2"], description: "An easy-to-pack hammock for the best part of a hike: finding a quiet place to stay awhile.", details: ["Parachute-soft recycled fabric", "Fast-hang tree-friendly straps", "Compact stuff sack included"] },
  { id: "atlas-binoculars", name: "Atlas Compact Trail Binoculars", category: "Outdoor", price: 139, rating: 4.7, reviews: 43, emoji: "🔭", image: "photo-1472396961693-142e6e269027", art: "art-lens", label: "LOOK CLOSER", colors: ["#e8e5d9", "#c7c2b4"], description: "Bring distant ridgelines and passing wildlife a little closer without weighing down your pack.", details: ["8× magnification", "Water-resistant rubber armor", "Pocket-size folding design"] },
  { id: "camera-case", name: "Canyon Waterproof Camera Case", category: "Accessories", price: 56, rating: 4.8, reviews: 71, emoji: "📸", image: "photo-1516035069371-29a1b244cc32", art: "art-sling", label: "KEEP IT SAFE", colors: ["#e8dfd3", "#c9b59f"], description: "A padded, weather-resistant home for your camera when the trail turns rough or the sky opens up.", details: ["Impact-resistant padded interior", "Weather-sealed roll-top closure", "Adjustable cross-body strap"] },
  { id: "polarizer-filter", name: "Clearwater Polarizing Lens Filter", category: "Camera gear", price: 45, rating: 4.7, reviews: 58, emoji: "🔍", image: "photo-1502920917128-1aa500764cbd", art: "art-lens", label: "PHOTO FAVORITE", colors: ["#e8e5d9", "#c7c2b4"], description: "Cut glare from water and glass while bringing a little more depth to bright outdoor scenes.", details: ["Multi-coated optical glass", "Low-profile aluminum frame", "Compatible with 49mm lenses"] },
  { id: "trail-headlamp", name: "Northline Rechargeable Headlamp", category: "Outdoor", price: 39, rating: 4.8, reviews: 114, emoji: "🔦", image: "photo-1500530855697-b586d89ba3ee", art: "art-camera", label: "AFTER DARK", colors: ["#dce6d8", "#a9b9a2"], description: "A comfortable, rechargeable headlamp for early starts, late returns, and camp after sunset.", details: ["USB-C rechargeable battery", "Adjustable wide-angle beam", "Lightweight moisture-resistant build"] },
  { id: "thermos-flask", name: "Evergreen Trail Thermos", category: "Outdoor", price: 34, rating: 4.7, reviews: 89, emoji: "☕", image: "photo-1511994298241-608e28f14fde", art: "art-pack", label: "WARM UP OUT THERE", colors: ["#e5e8d8", "#bdc7a8"], description: "A dependable insulated flask for the first coffee at the trailhead and the last sip at camp.", details: ["Insulated stainless steel", "Leak-resistant twist cap", "Easy-clean wide opening"] },
  { id: "camera-battery", name: "Summit X2 Spare Battery", category: "Camera gear", price: 59, rating: 4.8, reviews: 103, emoji: "🔋", image: "photo-1516035069371-29a1b244cc32", art: "art-lens", label: "DON'T MISS THE SHOT", colors: ["#e8e5d9", "#c7c2b4"], description: "One more full day of shooting when the views are too good to head back early.", details: ["Compatible with Summit X2", "USB-C fast charging", "Protective travel case included"] },
];

const CART_KEY = "northstar.store.cart";
const HISTORY_KEY = "northstar.store.history";
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
let storeMode = "offline";
let searchEventTimeout;
let recommendations = [];
const recommendationExposurePromises = new Map();
const recommendationObserver = "IntersectionObserver" in window
  ? new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting || entry.intersectionRatio < 0.5) return;
      const card = entry.target;
      recommendationObserver.unobserve(card);
      const offerId = card.dataset.offerId;
      const productId = card.dataset.productId;
      if (!offerId || !productId || recommendationExposurePromises.has(offerId)) return;
      recommendationExposurePromises.set(
        offerId,
        recordStoreEvent({
          event_type: "recommendation_impression",
          product_id: productId,
          offer_id: offerId,
        }),
      );
    });
  }, { threshold: 0.5 })
  : null;

function readStored(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "null");
    return value ?? fallback;
  } catch (error) {
    console.error(`Unable to read ${key} from browser storage.`, error);
    return fallback;
  }
}

function writeStored(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Unable to save ${key} to browser storage.`, error);
    showToast("Your browser could not save this update. Check storage settings.");
  }
}

function getProduct(id) {
  return products.find((product) => product.id === id);
}

function showStoreAlert(message) {
  let alert = document.querySelector("#store-status");
  if (!alert) {
    alert = document.createElement("div");
    alert.id = "store-status";
    alert.className = "store-status";
    alert.setAttribute("role", "status");
    document.querySelector(".store-header")?.after(alert);
  }
  alert.textContent = message;
  alert.hidden = !message;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`/api/store/${path}`, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Store API request failed (${response.status}).`);
  }
  return response.json();
}

async function recordStoreEvent(event) {
  if (storeMode !== "live") return false;
  try {
    await apiRequest("events", { method: "POST", body: JSON.stringify(event), keepalive: true });
    return true;
  } catch (error) {
    console.error("Unable to record storefront activity.", error);
    showStoreAlert("Some browsing activity could not be saved. Recommendations may be less personal.");
    return false;
  }
}

async function recordRecommendationClick(product) {
  if (storeMode !== "live" || !product.offer_id) return;
  let exposed = recommendationExposurePromises.get(product.offer_id);
  if (!exposed) {
    exposed = recordStoreEvent({
      event_type: "recommendation_impression",
      product_id: product.id,
      offer_id: product.offer_id,
    });
    recommendationExposurePromises.set(product.offer_id, exposed);
  }
  if (await exposed) {
    await recordStoreEvent({
      event_type: "recommendation_click",
      product_id: product.id,
      offer_id: product.offer_id,
    });
  }
}

async function loadLiveCatalog() {
  const catalog = await apiRequest("catalog");
  const displayProducts = new Map(products.map((product) => [product.id, product]));
  products = catalog.items.map((item) => {
    const presentation = displayProducts.get(item.product_id) || {
      reviews: 0,
      image: "photo-1516035069371-29a1b244cc32",
      art: "art-camera",
      label: "IN THE COLLECTION",
      colors: ["#dce6d8", "#a9b9a2"],
      description: `${item.name} from our ${item.category} collection.`,
      details: [],
    };
    return {
      ...presentation,
      id: item.product_id,
      name: item.name,
      category: item.category,
      price: item.price,
      rating: item.rating,
      emoji: item.emoji || presentation.emoji || "✳",
    };
  });
  const count = document.querySelector("#store-product-count");
  if (count) count.textContent = `${products.length} PIECES`;
}

async function loadLiveRecommendations() {
  const response = await apiRequest("recommendations");
  if (response.experiment_arm === "control") {
    showStoreAlert("Experiment group: top-rated product picks.");
  } else if (response.experiment_arm === "treatment") {
    showStoreAlert("Experiment group: personalized product picks.");
  }
  const items = response.items.map((item) => ({
    ...(getProduct(item.product_id) || {
      id: item.product_id,
      reviews: 0,
      image: "photo-1516035069371-29a1b244cc32",
      art: "art-camera",
      label: "IN THE COLLECTION",
      colors: ["#dce6d8", "#a9b9a2"],
      details: [],
    }),
    ...item,
    id: item.product_id,
  }));
  return items;
}

function getCart() {
  const cart = readStored(CART_KEY, {});
  return cart && typeof cart === "object" && !Array.isArray(cart) ? cart : {};
}

function setQuantity(id, quantity) {
  const cart = getCart();
  if (quantity > 0) cart[id] = Math.min(99, quantity);
  else delete cart[id];
  writeStored(CART_KEY, cart);
  updateCartCount();
  if (document.body.dataset.page === "cart") renderCart();
}

function updateCartCount() {
  const count = Object.values(getCart()).reduce((total, quantity) => total + Number(quantity || 0), 0);
  document.querySelectorAll("[data-cart-count]").forEach((element) => {
    element.textContent = String(count);
    element.classList.toggle("has-items", count > 0);
  });
}

let toastTimeout;
function showToast(message) {
  const toast = document.querySelector("#store-toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
}

function productCard(product, recommendation = false) {
  const card = document.createElement("article");
  card.className = "shop-card";
  if (recommendation && product.offer_id) {
    card.dataset.offerId = product.offer_id;
    card.dataset.productId = product.id;
  }
  const link = document.createElement("a");
  link.className = `shop-card-art ${product.art}`;
  link.href = `./product.html?id=${encodeURIComponent(product.id)}`;
  link.style.setProperty("--art-light", product.colors[0]);
  link.style.setProperty("--art-dark", product.colors[1]);
  link.setAttribute("aria-label", `View ${product.name}`);
  const label = document.createElement("span");
  label.className = "card-label";
  label.textContent = recommendation ? "JUST FOR YOU" : product.label;
  const emoji = document.createElement("span");
  emoji.className = "card-emoji image-fallback";
  emoji.textContent = product.emoji;
  emoji.hidden = true;
  const image = document.createElement("img");
  image.className = "card-photo";
  image.src = `https://images.unsplash.com/${product.image}?auto=format&fit=crop&w=720&q=82`;
  image.alt = "";
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.hidden = true;
    emoji.hidden = false;
  }, { once: true });
  const quickAdd = document.createElement("button");
  quickAdd.className = "quick-add";
  quickAdd.type = "button";
  quickAdd.textContent = "+";
  quickAdd.setAttribute("aria-label", `Add ${product.name} to bag`);
  quickAdd.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    void recordRecommendationClick(product);
    setQuantity(product.id, Number(getCart()[product.id] || 0) + 1);
    showToast(`${product.name} added to your bag.`);
  });
  link.append(label, image, emoji);
  card.append(link, quickAdd);
  const details = document.createElement("div");
  details.className = "shop-card-details";
  const category = document.createElement("span");
  category.className = "card-category";
  category.textContent = product.category;
  const name = document.createElement("a");
  name.className = "card-name";
  name.href = link.href;
  name.textContent = product.name;
  const meta = document.createElement("div");
  meta.className = "card-meta";
  const price = document.createElement("strong");
  price.textContent = currency.format(product.price);
  const rating = document.createElement("span");
  rating.textContent = `★ ${product.rating.toFixed(1)} (${product.reviews})`;
  meta.append(price, rating);
  details.append(category, name, meta);
  card.append(details);
  if (recommendation && product.reason) {
    const reason = document.createElement("p");
    reason.className = "recommendation-reason";
    reason.textContent = product.reason;
    details.append(reason);
  }
  if (recommendation) {
    if (storeMode === "live" && product.offer_id && recommendationObserver) {
      recommendationObserver.observe(card);
    }
    link.addEventListener("click", async (event) => {
      if (storeMode !== "live" || !product.offer_id) return;
      event.preventDefault();
      await recordRecommendationClick(product);
      window.location.assign(link.href);
    });
  }
  return card;
}

function renderProductGrid(target, items, recommendation = false) {
  target.replaceChildren(...items.map((product) => productCard(product, recommendation)));
}

function renderHome() {
  const grid = document.querySelector("#store-products");
  if (!grid) return;
  const search = document.querySelector("#store-search");
  const sort = document.querySelector("#store-sort");
  const empty = document.querySelector("#store-empty");
  const tabs = [...document.querySelectorAll(".category-tab")];
  document.querySelector('.category-tab[data-category="all"] span').textContent = String(products.length);
  const params = new URLSearchParams(window.location.search);
  let category = products.some((product) => product.category === params.get("category"))
    ? params.get("category")
    : "all";

  function update() {
    const query = search.value.trim().toLowerCase();
    const matches = products.filter((product) => {
      const matchesCategory = category === "all" || product.category === category;
      const matchesSearch = `${product.name} ${product.category}`.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    });
    if (sort.value === "price-low") matches.sort((a, b) => a.price - b.price);
    if (sort.value === "price-high") matches.sort((a, b) => b.price - a.price);
    if (sort.value === "rating") matches.sort((a, b) => b.rating - a.rating);
    renderProductGrid(grid, matches);
    empty.hidden = matches.length > 0;
    tabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.category === category));
  }

  tabs.forEach((tab) => tab.addEventListener("click", () => {
    category = tab.dataset.category;
    update();
  }));
  search.addEventListener("input", () => {
    update();
    window.clearTimeout(searchEventTimeout);
    const query = search.value.trim();
    if (query) {
      searchEventTimeout = window.setTimeout(() => {
        void recordStoreEvent({ event_type: "search", query });
      }, 600);
    }
  });
  sort.addEventListener("change", update);
  document.querySelectorAll("[data-show-all]").forEach((link) => link.addEventListener("click", () => {
    category = "all";
    search.value = "";
    update();
  }));
  update();
  void renderRecommendations();
}

document.querySelectorAll("[data-category-link]").forEach((link) => {
  link.href = link.dataset.categoryLink === "all"
    ? "./#shop"
    : `./?category=${encodeURIComponent(link.dataset.categoryLink)}#shop`;
});

function rememberProduct(product) {
  const history = readStored(HISTORY_KEY, []);
  const next = [product.id, ...history.filter((id) => id !== product.id)].slice(0, 8);
  writeStored(HISTORY_KEY, next);
}

async function renderRecommendations() {
  const target = document.querySelector("#store-recommendations");
  if (!target) return;
  if (storeMode === "live") {
    try {
      recommendations = await loadLiveRecommendations();
      target.dataset.anchor = recommendations[0]?.reason || "Recommendations for your visit";
      renderProductGrid(target, recommendations, true);
    } catch (error) {
      console.error("Unable to load live recommendations.", error);
      target.replaceChildren();
      showStoreAlert("Live recommendations are unavailable right now. Please try again shortly.");
    }
    return;
  }
  if (storeMode === "unavailable") {
    target.replaceChildren();
    return;
  }
  const history = readStored(HISTORY_KEY, []).map(getProduct).filter(Boolean);
  const anchor = history[0];
  const recommendations = products
    .filter((product) => !history.some((viewed) => viewed.id === product.id))
    .sort((a, b) => {
      const aRelated = anchor && (a.category === anchor.category ? 1 : 0);
      const bRelated = anchor && (b.category === anchor.category ? 1 : 0);
      return bRelated - aRelated || b.rating - a.rating;
    })
    .slice(0, 4);
  target.dataset.anchor = anchor ? `Since you viewed ${anchor.name}` : "A few customer favorites to get you started";
  renderProductGrid(target, recommendations.length ? recommendations : products.slice(0, 4), true);
}

function renderProductPage() {
  const id = new URLSearchParams(window.location.search).get("id");
  const product = getProduct(id);
  const target = document.querySelector("#product-detail");
  if (!product) {
    target.innerHTML = '<div class="not-found"><span>✳</span><h1>That gear wandered off.</h1><p>We could not find that product. Have a look around the collection instead.</p><a class="button button-dark" href="./#shop">Back to the shop <span aria-hidden="true">→</span></a></div>';
    document.querySelector(".related-section").hidden = true;
    return;
  }
  rememberProduct(product);
  void recordStoreEvent({ event_type: "product_view", product_id: product.id });
  document.title = `${product.name} — Northstar Goods`;
  document.querySelector("#product-breadcrumb").textContent = product.name;
  const layout = document.createElement("section");
  layout.className = "product-layout";
  const visual = document.createElement("div");
  visual.className = `product-detail-art ${product.art}`;
  visual.style.setProperty("--art-light", product.colors[0]);
  visual.style.setProperty("--art-dark", product.colors[1]);
  const label = document.createElement("span");
  label.className = "detail-label";
  label.textContent = product.label;
  const emoji = document.createElement("span");
  emoji.className = "detail-emoji image-fallback";
  emoji.textContent = product.emoji;
  emoji.hidden = true;
  const image = document.createElement("img");
  image.className = "detail-photo";
  image.src = `https://images.unsplash.com/${product.image}?auto=format&fit=crop&w=1100&q=85`;
  image.alt = product.name;
  image.addEventListener("error", () => {
    image.hidden = true;
    emoji.hidden = false;
  }, { once: true });
  visual.append(label, image, emoji);

  const info = document.createElement("div");
  info.className = "product-info";
  const category = document.createElement("p");
  category.className = "eyebrow";
  category.innerHTML = `<span></span>${product.category.toUpperCase()}`;
  const title = document.createElement("h1");
  title.textContent = product.name;
  const rating = document.createElement("div");
  rating.className = "detail-rating";
  rating.textContent = `★ ${product.rating.toFixed(1)} · ${product.reviews} field notes`;
  const price = document.createElement("p");
  price.className = "detail-price";
  price.textContent = currency.format(product.price);
  const description = document.createElement("p");
  description.className = "detail-description";
  description.textContent = product.description;
  const reason = document.createElement("div");
  reason.className = "personal-reason";
  const history = readStored(HISTORY_KEY, []).map(getProduct).filter(Boolean);
  reason.innerHTML = `<span>✳ A LITTLE PERSONALIZATION</span><p>${history.length > 1 && history[1].category === product.category ? `You've been exploring ${product.category.toLowerCase()}. We picked this as a good next look.` : `Selected from our ${product.category.toLowerCase()} collection. Browse a little and we will make these picks more personal.`}</p>`;
  const optionLabel = document.createElement("label");
  optionLabel.className = "quantity-label";
  optionLabel.textContent = "QUANTITY";
  const quantity = document.createElement("select");
  quantity.setAttribute("aria-label", "Quantity");
  for (let value = 1; value <= 5; value += 1) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = String(value);
    quantity.append(option);
  }
  optionLabel.append(quantity);
  const add = document.createElement("button");
  add.className = "button button-dark add-to-bag";
  add.type = "button";
  add.innerHTML = `Add to bag · ${currency.format(product.price)} <span aria-hidden="true">→</span>`;
  add.addEventListener("click", () => {
    setQuantity(product.id, Number(getCart()[product.id] || 0) + Number(quantity.value));
    showToast(`${product.name} added to your bag.`);
  });
  const assurances = document.createElement("div");
  assurances.className = "product-assurances";
  assurances.innerHTML = "<span>↗ Free shipping over $100</span><span>⌁ Easy 30-day returns</span>";
  const features = document.createElement("ul");
  features.className = "product-features";
  product.details.forEach((detail) => {
    const item = document.createElement("li");
    item.textContent = detail;
    features.append(item);
  });
  info.append(category, title, rating, price, description, reason, optionLabel, add, assurances, features);
  layout.append(visual, info);
  target.replaceChildren(layout);

  const related = products.filter((item) => item.id !== product.id && item.category === product.category);
  const extras = products.filter((item) => item.id !== product.id && item.category !== product.category);
  renderProductGrid(document.querySelector("#related-products"), [...related, ...extras].slice(0, 4));
}

function renderCart() {
  const target = document.querySelector("#cart-items");
  const summary = document.querySelector("#order-summary");
  if (!target || !summary) return;
  const cart = getCart();
  const items = Object.entries(cart)
    .map(([id, quantity]) => ({ product: getProduct(id), quantity: Number(quantity) }))
    .filter((item) => item.product && item.quantity > 0);
  target.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "empty-bag";
    empty.innerHTML = '<span>▱</span><h2>Your bag is taking a breather.</h2><p>Find something that makes you excited to get out the door.</p><a class="button button-dark" href="./#shop">Explore the collection <span aria-hidden="true">→</span></a>';
    target.append(empty);
    summary.hidden = true;
    return;
  }
  summary.hidden = false;
  items.forEach(({ product, quantity }) => {
    const row = document.createElement("article");
    row.className = "cart-row";
    const art = document.createElement("a");
    art.className = `cart-art ${product.art}`;
    art.href = `./product.html?id=${encodeURIComponent(product.id)}`;
    art.style.setProperty("--art-light", product.colors[0]);
    art.style.setProperty("--art-dark", product.colors[1]);
    art.textContent = product.emoji;
    const detail = document.createElement("div");
    detail.className = "cart-row-detail";
    const category = document.createElement("span");
    category.className = "card-category";
    category.textContent = product.category;
    const name = document.createElement("a");
    name.href = art.href;
    name.textContent = product.name;
    const price = document.createElement("strong");
    price.textContent = currency.format(product.price);
    detail.append(category, name, price);
    const controls = document.createElement("div");
    controls.className = "quantity-control";
    const decrement = document.createElement("button");
    decrement.type = "button";
    decrement.setAttribute("aria-label", `Remove one ${product.name}`);
    decrement.textContent = "−";
    decrement.addEventListener("click", () => setQuantity(product.id, quantity - 1));
    const count = document.createElement("span");
    count.textContent = String(quantity);
    const increment = document.createElement("button");
    increment.type = "button";
    increment.setAttribute("aria-label", `Add one ${product.name}`);
    increment.textContent = "+";
    increment.addEventListener("click", () => setQuantity(product.id, quantity + 1));
    controls.append(decrement, count, increment);
    const lineTotal = document.createElement("strong");
    lineTotal.className = "cart-line-total";
    lineTotal.textContent = currency.format(product.price * quantity);
    row.append(art, detail, controls, lineTotal);
    target.append(row);
  });

  const subtotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const shipping = subtotal >= 100 ? 0 : 8;
  summary.innerHTML = `<p class="eyebrow"><span></span> THE GOOD STUFF</p><h2>Order summary</h2><div class="summary-line"><span>Subtotal</span><strong>${currency.format(subtotal)}</strong></div><div class="summary-line"><span>Shipping</span><strong>${shipping === 0 ? "On us" : currency.format(shipping)}</strong></div><p class="shipping-note">${shipping === 0 ? "Your order ships free. Nice." : `Add ${currency.format(100 - subtotal)} more for free shipping.`}</p><div class="summary-total"><span>Total</span><strong>${currency.format(subtotal + shipping)}</strong></div><button class="button button-dark checkout-button" id="demo-checkout" type="button">Continue to checkout <span aria-hidden="true">→</span></button><small>Demo checkout only. No payment will be collected.</small>`;
  document.querySelector("#demo-checkout").addEventListener("click", () => {
    showToast("Demo store only — checkout and payment are not connected.");
  });
}

function initializeSearchShortcut() {
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      const search = document.querySelector("#store-search");
      if (search) {
        event.preventDefault();
        search.focus();
      }
    }
  });
}

async function initializeStore() {
  updateCartCount();
  initializeSearchShortcut();
  if (window.location.protocol !== "file:") {
    try {
      await apiRequest("session", { method: "POST", body: "{}" });
      await loadLiveCatalog();
      storeMode = "live";
    } catch (error) {
      storeMode = "unavailable";
      console.error("Unable to connect to the live store API.", error);
      showStoreAlert("The live store service is unavailable. Displaying the sample catalog; activity and recommendations are paused.");
    }
  } else {
    showStoreAlert("Offline preview: this page uses sample products and on-device demo recommendations.");
  }
  if (document.body.dataset.page === "home") renderHome();
  if (document.body.dataset.page === "product") renderProductPage();
  if (document.body.dataset.page === "cart") renderCart();
}

void initializeStore();
