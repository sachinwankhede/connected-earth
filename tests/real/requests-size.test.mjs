import * as H from '../app/helper.mjs';
import { defineRequestTests } from '../app/requests-suite.mjs';

// The same checks on the real build, with the request and kilobyte budgets (#787 step 4). Run on data pull requests and nightly, not in the app shards:
// sizes grow with the data, so only the real build can tell. Needs `npm run build` first.
defineRequestTests({ root: H.ROOT, title: 'the app reads only data we host (real build)', kb: true });
