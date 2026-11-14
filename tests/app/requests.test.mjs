import * as H from './helper.mjs';
import { defineRequestTests } from './requests-suite.mjs';

// Request counts and outside hosts on the frozen fixture build (#787). The kilobyte budgets are checked on the real build in tests/real/requests-size.test.mjs.
defineRequestTests({ root: H.FBUILD, title: 'the app reads only data we host (fixture build)', kb: false, prepare: () => H.fixtureBuild() });
