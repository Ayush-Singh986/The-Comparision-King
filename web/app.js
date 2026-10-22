const config = window.NORTHSTAR_CONFIG || {};
const liveMode = Boolean(config.userPoolId && config.appClientId && config.cognitoDomain && !config.sampleMode);
const productCards = [...document.querySelectorAll(".product-card")];
const filterButtons = [...document.querySelectorAll(".filter-chip")];
const searchInput = document.querySelector("#product-search");
const emptyProducts = document.querySelector("#empty-products");
const toast = document.querySelector("#toast");
const authGate = document.querySelector("#auth-gate");
const detailDialog = document.querySelector("#detail-dialog");
const detailAction = document.querySelector("#detail-action");
let selectedFilter = "all";
let toastTimeout;
let currentActivityDays = 7;
let accessToken = "";
const catalogDivider = document.createElement("div");
catalogDivider.className = "catalog-divider";
catalogDivider.textContent = "More from the collection";
catalogDivider.hidden = true;
const productDescriptions = {
  "camera-x2": "A versatile mirrorless camera for outdoor trips, travel, and everyday photography.",
  "trail-pack-28": "A lightweight 28-liter daypack with room for camera gear and trail essentials.",
  "prime-lens-50": "A bright 50mm prime lens for portraits, low-light scenes, and crisp detail.",
  "camera-sling": "A compact padded sling that keeps a camera and daily essentials close at hand.",
  "trail-shell": "A packable waterproof shell for changing weather on hikes and day trips.",
  "summit-boots": "Supportive hiking boots with grippy soles for rocky trails and long walks.",
  "carbon-tripod": "A travel-ready carbon tripod for steady landscapes and low-light photos.",
  "field-drive": "A portable 1TB solid-state drive for backing up photos while traveling.",
};
const today = new Date();
document.querySelectorAll(".match-row > span").forEach((label) => {
  label.textContent = "Ranking score (not probability)";
});
document.querySelector("#current-date").textContent = new Intl.DateTimeFormat("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
}).format(today).toUpperCase();

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

function showProductDetails(card) {
  const productId = card.dataset.productId;
  const price = card.querySelector(".product-meta > strong").textContent;
  const rating = card.querySelector(".product-meta > span").textContent;
  document.querySelector("#detail-eyebrow").textContent = "PRODUCT DETAILS";
  document.querySelector("#detail-visual").textContent =
    card.querySelector(".product-emoji").textContent;
  document.querySelector("#detail-category").textContent = card.dataset.category.toUpperCase();
  document.querySelector("#detail-title").textContent = card.dataset.name;
  document.querySelector("#detail-price").textContent = price;
  document.querySelector("#detail-rating").textContent = rating;
  document.querySelector("#detail-description").textContent =
    productDescriptions[productId] || "A catalog product selected for this shopper's recent interests.";
  const isRecommendation = card.dataset.recommendationKind !== "catalog";
  document.querySelector("#detail-reason-title").textContent = isRecommendation
    ? "Why this was recommended"
    : "From the store catalog";
  document.querySelector("#detail-reason").textContent =
    card.querySelector(".product-reason").textContent.trim();
  document.querySelector("#detail-note").textContent = liveMode
    ? "Store operations preview. Product pages and checkout are on the separate storefront."
    : "Sample catalog item. Product pages and checkout are on the separate storefront.";
  document.querySelector("#detail-price").hidden = false;
  document.querySelector("#detail-rating").hidden = false;
  detailAction.textContent = "Explore related products →";
  detailDialog.dataset.relatedCategory = card.dataset.category;
  detailDialog.dataset.destination = "recommendations";
  detailDialog.showModal();
}

function exploreRelatedProducts() {
  const category = detailDialog.dataset.relatedCategory;
  detailDialog.close();
  selectedFilter = "all";
  filterButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.filter === "all"));
  searchInput.value = category || "";
  filterProducts();
  const destination = detailDialog.dataset.destination || "recommendations";
  window.location.hash = destination;
  document.querySelector(`#${destination}`).scrollIntoView({ behavior: "smooth", block: "start" });
}

function filterProducts() {
  const query = searchInput.value.trim().toLowerCase();
  let visibleCount = 0;

  productCards.forEach((card) => {
    const matchesQuery = card.dataset.name.toLowerCase().includes(query)
      || card.dataset.category.toLowerCase().includes(query);
    const matchesFilter = selectedFilter === "all"
      || card.dataset.signal.split(" ").includes(selectedFilter);
    card.hidden = !matchesQuery || !matchesFilter;
    if (!card.hidden) visibleCount += 1;
  });

  emptyProducts.hidden = visibleCount > 0;
  catalogDivider.hidden = !productCards.some((card) => !card.hidden && card.dataset.recommendationKind === "catalog");
}

function updateActivityChart(activity, days) {
  const groups = document.querySelector("#activity-bars");
  const yLabels = [...document.querySelectorAll(".chart-y-axis span")];
  const rows = activity.slice(-7);
  const maximum = Math.max(4, ...rows.flatMap((row) => [row.views, row.purchases]));
  const axisMaximum = Math.ceil(maximum / 4);
  yLabels.forEach((label, index) => {
    label.textContent = index === 4
      ? "0"
      : Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 })
        .format(axisMaximum * (4 - index));
  });

  groups.replaceChildren();
  rows.forEach((row) => {
    const group = document.createElement("div");
    group.className = "bar-group";
    const pair = document.createElement("div");
    pair.className = "bar-pair";
    const viewBar = document.createElement("i");
    const purchaseBar = document.createElement("i");
    purchaseBar.className = "purchase-bar";
    viewBar.style.height = `${Math.max(2, row.views / (axisMaximum * 4) * 100)}%`;
    purchaseBar.style.height = `${Math.max(2, row.purchases / (axisMaximum * 4) * 100)}%`;
    pair.append(viewBar, purchaseBar);
    const label = document.createElement("span");
    const date = new Date(`${row.day}T12:00:00`);
    label.textContent = days === 30
      ? new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date)
      : new Intl.DateTimeFormat("en-US", { weekday: "short" }).format(date);
    group.append(pair, label);
    groups.append(group);
  });
  document.querySelector(".chart").setAttribute(
    "aria-label",
    `Customer product views and purchases over the last ${days} days`,
  );
}

function updateSummary(data) {
  document.querySelector("#metric-events").textContent = Number(data.events_7d).toLocaleString();
  document.querySelector("#metric-ctr").textContent = Number(data.ctr_percent).toFixed(2);
  document.querySelector("#metric-products").textContent = Number(data.product_count).toLocaleString();
  document.querySelector("#metric-top-category").textContent = data.top_category || "No activity yet";
  document.querySelector("#metric-latency").textContent = Number(data.avg_latency_ms).toLocaleString();
  document.querySelector("#metric-cache-hit").textContent = `${Number(data.cache_hit_percent)}%`;
  document.querySelector("#activity-total").textContent = Number(data.events_7d).toLocaleString();
  document.querySelector(".activity-summary > span:nth-child(2)").textContent = "store-wide interactions";
  updateActivityChart(data.activity, currentActivityDays);
  renderTrendingCategories(data.trending_categories);
  renderExperiment(data.experiment);
}

function renderExperiment(experiment) {
  if (!experiment) return;
  const number = (value) => Number(value || 0).toLocaleString();
  const percent = (value) => `${Number(value || 0).toFixed(2)}%`;
  ["control", "treatment"].forEach((arm) => {
    const metrics = experiment.arms[arm];
    document.querySelector(`#experiment-${arm}-assigned`).textContent = number(metrics.assigned_sessions);
    document.querySelector(`#experiment-${arm}-exposed`).textContent = number(metrics.exposed_sessions);
    document.querySelector(`#experiment-${arm}-impressions`).textContent = number(metrics.impressions);
    document.querySelector(`#experiment-${arm}-clicks`).textContent = number(metrics.clicks);
    document.querySelector(`#experiment-${arm}-ctr`).textContent = percent(metrics.ctr_percent);
    document.querySelector(`#experiment-${arm}-ctr-ci`).textContent =
      formatInterval(metrics.ctr_95ci_percent);
    document.querySelector(`#experiment-${arm}-orders`).textContent = number(metrics.purchasing_sessions);
    document.querySelector(`#experiment-${arm}-conversion`).textContent = percent(metrics.conversion_percent);
    document.querySelector(`#experiment-${arm}-sales`).textContent =
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
      }).format(Number(metrics.gross_sales_usd || 0));
    document.querySelector(`#experiment-${arm}-conversion-ci`).textContent =
      formatInterval(metrics.conversion_95ci_percent);
  });
  function formatInterval(interval) {
    return interval
      ? `${Number(interval[0]).toFixed(2)}–${Number(interval[1]).toFixed(2)}%`
      : "Not available";
  }
  const change = (value) => value === null
    ? "Not available"
    : `${value > 0 ? "+" : ""}${Number(value).toFixed(2)}%`;
  document.querySelector("#experiment-ctr-change").textContent =
    change(experiment.treatment_ctr_relative_change_percent);
  document.querySelector("#experiment-conversion-change").textContent =
    change(experiment.treatment_conversion_relative_change_percent);
  document.querySelector("#experiment-caveat").textContent =
    `${experiment.interpretation} Verified gross order value excludes refunds, cancellations, cost of goods, and payment fees. Wilson intervals are descriptive, not a significance test.`;
}

function renderTrendingCategories(categories) {
  const list = document.querySelector("#trend-list");
  const categoryIcons = {
    "Camera gear": ["📷", "art-camera"],
    Outdoor: ["🥾", "art-trail"],
    Accessories: ["🎒", "art-sling"],
  };
  list.replaceChildren();
  categories.forEach((category, index) => {
    const [emoji, artClass] = categoryIcons[category.category] || ["✳", "art-camp"];
    const row = document.createElement("button");
    row.type = "button";
    row.className = "trend-item trend-item-button";
    row.dataset.category = category.category;
    const rank = document.createElement("span");
    rank.className = "trend-rank";
    rank.textContent = String(index + 1).padStart(2, "0");
    const art = document.createElement("span");
    art.className = `trend-art ${artClass}`;
    art.textContent = emoji;
    const copy = document.createElement("span");
    copy.className = "trend-copy";
    const title = document.createElement("strong");
    title.textContent = category.category;
    const views = document.createElement("small");
    views.textContent = `${Number(category.views_7d).toLocaleString()} views this week`;
    copy.append(title, views);
    const growth = document.createElement("span");
    growth.className = "trend-growth";
    growth.textContent = category.growth_percent === null
      ? "NEW"
      : `↗ ${category.growth_percent}%`;
    row.append(rank, art, copy, growth);
    list.append(row);
  });
  if (!categories.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Product trends will appear as customers browse.";
    list.append(empty);
  }
}

function updateRecommendedProducts(items) {
  const grid = document.querySelector("#product-grid");
  const cardsById = new Map(productCards.map((card) => [card.dataset.productId, card]));
  const recommendations = items.filter((item) => cardsById.has(item.product_id));
  document.querySelector("#nav-count").textContent = String(recommendations.length);
  catalogDivider.hidden = true;
  productCards.forEach((card) => {
    card.hidden = true;
    card.dataset.recommendationKind = "catalog";
    card.querySelector(".match-row").hidden = true;
    card.querySelector(".match-track").hidden = true;
    card.querySelector(".product-open").innerHTML = 'View product details <span aria-hidden="true">→</span>';
  });
  recommendations.forEach((item, index) => {
    const card = cardsById.get(item.product_id);
    card.dataset.recommendationKind = "recommended";
    card.dataset.name = item.name;
    card.dataset.category = item.category;
    card.querySelector("h3").textContent = item.name;
    card.querySelector(".product-category").textContent = item.category.toUpperCase();
    card.querySelector(".product-meta > strong").textContent = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(Number(item.price));
    card.querySelector(".product-meta > span").textContent = `★ ${Number(item.rating).toFixed(1)} · catalog`;
    const rankingScore = Math.round(item.score * 100);
    card.querySelector(".match-row > strong").textContent = `${rankingScore}/100`;
    card.querySelector(".match-row").hidden = false;
    card.querySelector(".match-track").hidden = false;
    card.querySelector(".match-track i").style.width = `${rankingScore}%`;
    card.querySelector(".product-reason").textContent = `✳ ${item.reason}`;
    const badge = card.querySelector(".product-trend, .product-tag");
    badge.textContent = `RANK ${rankingScore}/100`;
    card.querySelector(".product-open").innerHTML = 'See why recommended <span aria-hidden="true">→</span>';
    card.hidden = false;
    card.style.order = String(index);
    grid.append(card);
  });
  const remainingCards = productCards.filter((card) => card.dataset.recommendationKind === "catalog");
  if (remainingCards.length) {
    catalogDivider.style.order = String(recommendations.length);
    grid.append(catalogDivider);
    remainingCards.forEach((card, index) => {
      card.querySelector(".product-reason").textContent = "From the full Northstar store collection.";
      card.querySelector(".product-trend, .product-tag").textContent = "IN COLLECTION";
      card.hidden = false;
      card.style.order = String(recommendations.length + index + 1);
      grid.append(card);
    });
  }
  filterProducts();
}

async function exchangeCode(code, returnedState) {
  const savedState = sessionStorage.getItem("northstar.oauth.state");
  const verifier = sessionStorage.getItem("northstar.oauth.verifier");
  sessionStorage.removeItem("northstar.oauth.state");
  sessionStorage.removeItem("northstar.oauth.verifier");
  if (!savedState || returnedState !== savedState || !verifier) {
    throw new Error("Sign-in could not be verified. Please try again.");
  }
  const response = await fetch(`${config.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: config.appClientId,
      code,
      redirect_uri: config.redirectUri,
      code_verifier: verifier,
    }),
  });
  const tokens = await response.json();
  if (!response.ok || !tokens.access_token) {
    throw new Error(tokens.error_description || "Sign-in could not be completed.");
  }
  saveTokens(tokens);
}

function saveTokens(tokens) {
  accessToken = tokens.access_token;
  sessionStorage.setItem("northstar.access-token", accessToken);
  sessionStorage.setItem(
    "northstar.access-expiry",
    String(Date.now() + Number(tokens.expires_in || 3600) * 1000),
  );
  if (tokens.refresh_token) {
    sessionStorage.setItem("northstar.refresh-token", tokens.refresh_token);
  }
}

async function getAccessToken() {
  const expiresAt = Number(sessionStorage.getItem("northstar.access-expiry") || 0);
  if (accessToken && expiresAt > Date.now() + 60_000) return accessToken;
  const savedToken = sessionStorage.getItem("northstar.access-token");
  if (savedToken && expiresAt > Date.now() + 60_000) {
    accessToken = savedToken;
    return accessToken;
  }
  const refreshToken = sessionStorage.getItem("northstar.refresh-token");
  if (!refreshToken) return "";
  const response = await fetch(`${config.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: config.appClientId,
      refresh_token: refreshToken,
    }),
  });
  const tokens = await response.json();
  if (!response.ok || !tokens.access_token) {
    clearSession();
    return "";
  }
  saveTokens(tokens);
  return accessToken;
}

function clearSession() {
  for (const key of [
    "northstar.access-token",
    "northstar.access-expiry",
    "northstar.refresh-token",
    "northstar.oauth.state",
    "northstar.oauth.verifier",
  ]) {
    sessionStorage.removeItem(key);
  }
  accessToken = "";
}

function showSignedOutState() {
  authGate.hidden = false;
  document.querySelector("#auth-button").textContent = "Sign in";
  document.querySelector("#account-button").setAttribute("aria-label", "Sign in");
  document.querySelector("#environment-chip").lastChild.textContent = " SIGN IN REQUIRED";
}

function showSignedInState() {
  authGate.hidden = true;
  document.querySelector("#auth-button").textContent = "Sign out";
  document.querySelector("#account-button").setAttribute("aria-label", "Sign out");
  document.querySelector("#environment-chip").lastChild.textContent = " CONNECTED";
  document.querySelector("#aws-status-title").textContent = "AWS connected";
  document.querySelector("#aws-status-detail").textContent = "Live events and recommendations";
}

function startSignIn() {
  const verifierBytes = crypto.getRandomValues(new Uint8Array(32));
  const verifier = bytesToBase64Url(verifierBytes);
  const state = bytesToBase64Url(crypto.getRandomValues(new Uint8Array(32)));
  sessionStorage.setItem("northstar.oauth.state", state);
  sessionStorage.setItem("northstar.oauth.verifier", verifier);
  crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)).then((digest) => {
    const challenge = bytesToBase64Url(new Uint8Array(digest));
    const authorizeUrl = new URL(`${config.cognitoDomain}/oauth2/authorize`);
    authorizeUrl.search = new URLSearchParams({
      client_id: config.appClientId,
      response_type: "code",
      scope: "openid email profile",
      redirect_uri: config.redirectUri,
      code_challenge_method: "S256",
      code_challenge: challenge,
      state,
    });
    window.location.assign(authorizeUrl);
  }).catch((error) => {
    console.error("Unable to start secure sign-in.", error);
    showToast("Secure sign-in could not be started. Please retry.");
  });
}

function bytesToBase64Url(bytes) {
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function signOut() {
  clearSession();
  const logoutUrl = new URL(`${config.cognitoDomain}/logout`);
  logoutUrl.search = new URLSearchParams({
    client_id: config.appClientId,
    logout_uri: config.redirectUri,
  });
  window.location.assign(logoutUrl);
}

class ApiError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.statusCode = statusCode;
  }
}

async function apiRequest(path, options = {}) {
  const token = await getAccessToken();
  if (!token) {
    showSignedOutState();
    throw new ApiError(401, "Sign in to load live commerce data.");
  }
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const body = await response.json();
  if (response.status === 401) {
    clearSession();
    showSignedOutState();
  }
  if (!response.ok) {
    throw new ApiError(response.status, body.detail || "The AWS application request failed.");
  }
  return body;
}

async function refreshLiveData(days = currentActivityDays) {
  const recommendations = await apiRequest("/recommendations");
  updateRecommendedProducts(recommendations.items);
  const summary = await apiRequest(`/summary?days=${days}`);
  currentActivityDays = days;
  updateSummary(summary);
  renderRecentEvents(summary.recent_events);
}

function renderRecentEvents(events) {
  const list = document.querySelector("#signal-list");
  const icons = {
    product_view: ["◉", "signal-view", "Product viewed"],
    recommendation_impression: ["✳", "signal-view", "Recommendation shown"],
    recommendation_click: ["↗", "signal-cart", "Recommendation clicked"],
    purchase: ["✓", "signal-buy", "Purchase completed"],
    search: ["⌕", "signal-search", "Search performed"],
  };
  list.replaceChildren();
  events.forEach((event) => {
    const [icon, iconClass, title] = icons[event.event_type] || ["◉", "signal-view", "Customer activity"];
    const row = document.createElement("div");
    row.className = "signal-item";
    const eventIcon = document.createElement("span");
    eventIcon.className = `signal-icon ${iconClass}`;
    eventIcon.textContent = icon;
    const copy = document.createElement("span");
    copy.className = "signal-copy";
    const eventTitle = document.createElement("strong");
    eventTitle.textContent = title;
    const description = document.createElement("small");
    description.textContent = event.product_name || event.query || "Store customer";
    copy.append(eventTitle, description);
    const time = document.createElement("time");
    time.dateTime = event.created_at;
    time.textContent = formatRelativeTime(event.created_at);
    row.append(eventIcon, copy, time);
    list.append(row);
  });
  if (!events.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Customer activity will appear here as events arrive.";
    list.append(empty);
  }
}

function formatRelativeTime(timestamp) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000));
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

async function initializeLiveApp() {
  authGate.hidden = false;
  document.querySelector("#auth-button").hidden = false;
  document.querySelector("#account-button").hidden = true;
  document.querySelector("#auth-login").addEventListener("click", startSignIn);
  const authButton = document.querySelector("#auth-button");
  const accountButton = document.querySelector("#account-button");
  authButton.addEventListener("click", () => {
    if (accessToken || sessionStorage.getItem("northstar.refresh-token")) signOut();
    else startSignIn();
  });
  accountButton.addEventListener("click", signOut);

  try {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    if (code) {
      await exchangeCode(code, state);
      url.searchParams.delete("code");
      url.searchParams.delete("state");
      url.searchParams.delete("session_state");
      window.history.replaceState({}, document.title, url);
    }
    if (!await getAccessToken()) {
      showSignedOutState();
      return;
    }
    showSignedInState();
    await refreshLiveData(7);
  } catch (error) {
    console.error("Unable to initialize the live commerce dashboard.", error);
    showSignedOutState();
    showToast(error.message || "Unable to load live data. Please try again.");
  }
}

function updateLocalActivityChart(isMonth) {
  const groups = [...document.querySelectorAll("#activity-bars .bar-group")];
  const bars = groups.map((group) => group.querySelector(".bar-pair"));
  const monthHeights = [[62, 26], [45, 17], [74, 31], [57, 22], [84, 39], [68, 29], [91, 43]];
  const weekHeights = [[54, 20], [67, 26], [48, 18], [74, 34], [62, 25], [86, 40], [70, 31]];
  const dateLabels = Array.from({ length: 5 }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (4 - index) * 7);
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
  });

  groups.forEach((group, index) => {
    group.hidden = isMonth && index >= dateLabels.length;
    group.querySelector("span").textContent = isMonth
      ? dateLabels[index]
      : new Intl.DateTimeFormat("en-US", { weekday: "short" })
        .format(new Date(today.getFullYear(), today.getMonth(), today.getDate() - 6 + index));
  });
  bars.forEach((pair, index) => {
    pair.children[0].style.height = `${(isMonth ? monthHeights : weekHeights)[index][0]}%`;
    pair.children[1].style.height = `${(isMonth ? monthHeights : weekHeights)[index][1]}%`;
  });
  document.querySelector(".chart").setAttribute(
    "aria-label",
    `Customer product views and purchases over the selected ${isMonth ? "30 days" : "seven days"}`,
  );
}

searchInput.addEventListener("input", () => {
  filterProducts();
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    selectedFilter = button.dataset.filter;
    filterButtons.forEach((item) => item.classList.toggle("is-active", item === button));
    filterProducts();
  });
});

const navigationTitles = {
  overview: "Overview",
  recommendations: "Recommendations",
  experiment: "Experiment results",
  customers: "Customers",
  trends: "Trending products",
  activity: "Event activity",
};

document.querySelectorAll("[data-nav]").forEach((link) => {
  link.addEventListener("click", () => {
    const section = link.dataset.nav;
    document.querySelectorAll("[data-nav]").forEach((item) => {
      item.classList.toggle("is-active", item === link);
    });
    document.querySelector("#breadcrumb-title").textContent = navigationTitles[section];
  });
});

document.querySelector("#refresh-recommendations").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.querySelector(".refresh-icon").classList.add("is-spinning");
  try {
    if (liveMode) {
      await refreshLiveData(currentActivityDays);
      showToast("Personalized recommendations refreshed.");
    } else {
      showToast("Sample recommendations refreshed.");
    }
  } catch (error) {
    console.error("Recommendation refresh failed.", error);
    showToast(error.message || "Recommendations could not be refreshed.");
  } finally {
    button.disabled = false;
    button.querySelector(".refresh-icon").classList.remove("is-spinning");
  }
});

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".segment").forEach((item) => item.classList.toggle("is-selected", item === button));
    const days = Number(button.dataset.range);
    if (liveMode) {
      try {
        currentActivityDays = days;
        updateSummary(await apiRequest(`/summary?days=${days}`));
      } catch (error) {
        console.error("Activity summary could not be loaded.", error);
        showToast(error.message || "Activity summary could not be loaded.");
      }
    } else {
      updateLocalActivityChart(days === 30);
    }
  });
});

document.querySelector("#view-all-recommendations").addEventListener("click", () => {
  selectedFilter = "all";
  searchInput.value = "";
  filterButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.filter === "all"));
  filterProducts();
  document.querySelector("#recommendations").scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#product-grid").addEventListener("click", (event) => {
  const card = event.target.closest(".product-card");
  if (!card) return;
  const button = event.target.closest("button");
  if (button && !button.matches(".product-open, .product-more")) return;
  showProductDetails(card);
});

document.querySelector("#trend-list").addEventListener("click", (event) => {
  const trend = event.target.closest(".trend-item-button");
  if (!trend) return;
  selectedFilter = "all";
  filterButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.filter === "all"));
  searchInput.value = trend.dataset.category;
  filterProducts();
  window.location.hash = "recommendations";
  document.querySelector("#recommendations").scrollIntoView({ behavior: "smooth", block: "start" });
});

detailAction.addEventListener("click", exploreRelatedProducts);
document.querySelector("#detail-close").addEventListener("click", () => detailDialog.close());
detailDialog.addEventListener("click", (event) => {
  if (event.target === detailDialog) detailDialog.close();
});

document.querySelectorAll(".date-button, .more-button, .icon-more").forEach((button) => {
  button.addEventListener("click", () => showToast("This control is a preview in the sample dashboard."));
});

if (liveMode) {
  initializeLiveApp();
} else {
  authGate.hidden = true;
  document.querySelector("#account-button").addEventListener("click", () => {
    showToast("This control is a preview in the sample dashboard.");
  });
  filterProducts();
}
