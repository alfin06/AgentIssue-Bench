<template>
  <div class="d-flex flex-column min-vh-100">
    <!-- Header -->
    <header class="bg-dark text-white py-3 shadow-sm w-100 px-3">
      <div class="d-flex justify-content-between align-items-center">
        <h2 class="mb-0">🤖 AgentIssue-Bench</h2>
        <nav>
          <a href="/leaderboard" class="btn btn-outline-light btn-sm">Leaderboard</a>
        </nav>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-fill px-3 py-4 w-100">
      <div class="text-center mb-4">
        <h1 class="display-5 fw-bold">🏆 Leaderboard</h1>
        <p class="text-muted">Top-performing SE agent systems ranked by % Resolved</p>
      </div>

      <div class="card shadow-sm rounded-4 w-100">
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-striped table-hover mb-0 align-middle text-center w-100">
              <thead class="table-dark">
                <tr>
                  <th scope="col" @click="sortBy('rank')" style="cursor:pointer;">
                    Rank
                    <SortIcon :field="'rank'" :currentSort="sortKey" :direction="sortDirection" />
                  </th>
                  <th scope="col" @click="sortBy('system')" style="cursor:pointer;">
                    Model
                    <SortIcon :field="'system'" :currentSort="sortKey" :direction="sortDirection" />
                  </th>
                  <th scope="col" @click="sortBy('institution')" style="cursor:pointer;">
                    Institution
                    <SortIcon :field="'institution'" :currentSort="sortKey" :direction="sortDirection" />
                  </th>
                  <th scope="col" @click="sortBy('score')" style="cursor:pointer;">
                    % Resolved
                    <SortIcon :field="'score'" :currentSort="sortKey" :direction="sortDirection" />
                  </th>
                  <th scope="col">Link</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, index) in paginatedData" :key="entry.system">
                  <th scope="row" class="text-primary">{{ index + 1 + (currentPage - 1) * pageSize }}</th>
                  <td><strong>{{ entry.system }}</strong></td>
                  <td><img :src="entry.institution" :alt="entry.system + ' institution logo'" style="height: 1.5em;" /></td>
                  <td>
                    <span class="badge bg-success fs-6 px-3 py-2">{{ entry.score.toFixed(2) }}</span>
                  </td>
                  <td>
                    <a
                      :href="entry.link"
                      target="_blank"
                      rel="noopener"
                      class="btn btn-sm btn-outline-primary">
                      View
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination controls -->
          <nav aria-label="Page navigation" class="my-3 d-flex justify-content-center">
            <ul class="pagination mb-0">
              <li
                class="page-item"
                :class="{ disabled: currentPage === 1 }"
                @click="changePage(currentPage - 1)">
                <a class="page-link" href="#" tabindex="-1">Previous</a>
              </li>
              <li
                v-for="page in totalPages"
                :key="page"
                class="page-item"
                :class="{ active: currentPage === page }"
                @click="changePage(page)">
                <a class="page-link" href="#">{{ page }}</a>
              </li>
              <li
                class="page-item"
                :class="{ disabled: currentPage === totalPages }"
                @click="changePage(currentPage + 1)">
                <a class="page-link" href="#">Next</a>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      <br />
      <div class="card shadow-sm rounded-4 w-100">
        <div class="card-body p-0">
          <div class="text-center mb-4">
            <h1 class="display-5 fw-bold">Resolution Rate</h1>
            <hr/>
          </div>
          <div>
            <img :src="bar" alt="bar" style="width: 100%;" />
          </div>
        </div>
      </div>

      <br/>
      <div class="card shadow-sm rounded-4 w-100">
        <div class="card-body p-0">
            <div class="text-center mb-4">
              <h1 class="display-5 fw-bold">News</h1>
              <hr/>
            </div>
            <div>
              <ul>
                <li>[05/2025] Initial benchmark release</li>
              </ul>
            </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-light text-center py-3 mt-auto border-top w-100 px-0">
      <div class="px-3">
        <small class="text-muted">© 2025 AgentIssue-Bench Team. All rights reserved.</small>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import Bar from "../assets/images/bar.png";

// Sort icon component for visual indication
const SortIcon = {
  props: ['field', 'currentSort', 'direction'],
  template: `
    <span v-if="currentSort === field">
      <i v-if="direction === 'asc'" class="bi bi-arrow-up-short"></i>
      <i v-else class="bi bi-arrow-down-short"></i>
    </span>
  `,
};

const leaderboard = ref([
  {
    system: 'AutoCodeRover + Claude 3.5 Sonnet',
    institution: 'https://avatars.githubusercontent.com/u/100131783?s=200&v=4',
    score: 12.67,
    link: 'https://autocoderover.dev/',
  },
  {
    system: 'Agentless  + Claude 3.5 Sonnet',
    institution: 'https://brand.illinois.edu/wp-content/uploads/2024/02/Color-Variation-Orange-Block-I-White-Background.png',
    score: 8.67,
    link: 'https://github.com/OpenAutoCoder/Agentless',
  },
  {
    system: 'SWE-agent  + Claude 3.5 Sonnet',
    institution: 'https://avatars.githubusercontent.com/u/166046056?s=200&v=4',
    score: 6.67,
    link: 'https://swe-agent.com/',
  },
  {
    system: 'Agentless  + GPT-4o',
    institution: 'https://brand.illinois.edu/wp-content/uploads/2024/02/Color-Variation-Orange-Block-I-White-Background.png',
    score: 6.00,
    link: 'https://github.com/OpenAutoCoder/Agentless',
  },
  {
    system: 'AutoCodeRover + GPT-4o',
    institution: 'https://avatars.githubusercontent.com/u/100131783?s=200&v=4',
    score: 4.67,
    link: 'https://autocoderover.dev/',
  },
  {
    system: 'SWE-agent  + GPT-4o',
    institution: 'https://avatars.githubusercontent.com/u/166046056?s=200&v=4',
    score: 3.33,
    link: 'https://swe-agent.com/',
  },
]);

const sortKey = ref('score');
const sortDirection = ref('desc');
const currentPage = ref(1);
const pageSize = 10;
const bar = Bar;

function sortBy(field) {
  if (sortKey.value === field) {
    // toggle direction
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = field;
    sortDirection.value = 'asc';
  }
  currentPage.value = 1; // reset to first page on sort
}

const sortedData = computed(() => {
  return [...leaderboard.value].sort((a, b) => {
    let aVal, bVal;
    if (sortKey.value === 'rank') {
      aVal = leaderboard.value.indexOf(a);
      bVal = leaderboard.value.indexOf(b);
    } else {
      aVal = a[sortKey.value];
      bVal = b[sortKey.value];
    }

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const totalPages = computed(() => Math.ceil(sortedData.value.length / pageSize));

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return sortedData.value.slice(start, start + pageSize);
});

function changePage(page) {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
}
</script>

<style>
/* Remove horizontal padding/margins from main wrappers for full width */
html, body, #app {
  margin: 0;
  margin-left: 15%;
  padding: 0;
  height: 100%;
  width:100%;
}

/* Cursor pointer for sortable headers */
th {
  user-select: none;
}
</style>
