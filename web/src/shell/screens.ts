/**
 * The screens, their paths and their Persian names.
 *
 * One list, used by the navigation, the router and the page title, so a screen
 * cannot exist in the menu and nowhere else. docs/FRONTEND.md settles that all
 * seven are built rather than a subset; *word detail* is reached by clicking a
 * result rather than from the menu, so it is here but not in the navigation.
 */

export interface Screen {
  path: string;
  /** What the menu says. */
  label: string;
  /** The heading, and what the browser tab says. */
  title: string;
  /** The one line under the heading: what this screen is for. */
  purpose: string;
  /**
   * Three or four words in the menu, under the name.
   *
   * The names are nouns — ساخت، ترکیب، تحلیل — and a first-time reader cannot
   * tell them apart, which the project lead raised on 2026-08-17: *the names
   * do not say what they do*. `purpose` is a sentence and belongs under the
   * heading; this is the short form the menu has room for. Shown rather than
   * hidden behind a hover, because the reader who needs it is on a phone
   * deciding where to go, and a phone has no hover.
   */
  gloss: string;
  /** What to do when there is nothing on screen yet. */
  invitation: string;
  /** False for a screen reached from another one rather than from the menu. */
  inNavigation: boolean;
  /** Which PLAN task builds it. */
  task: string;
}

export const SCREENS: Screen[] = [
  {
    path: "/",
    gloss: "واژه‌ها را پیدا کنید",
    label: "جست‌وجو",
    title: "جست‌وجو",
    purpose:
      "دنبال واژه بگردید: با چند حرف از آن، با وند یا بنش، با گونه‌اش، یا با اینکه چند بار و در کدام سده آمده است.",
    invitation: "بنویسید دنبال چه هستید، مثلاً واژه‌هایی که با «نا» تمام می‌شوند.",
    inNavigation: true,
    task: "۷.۲",
  },
  {
    path: "/word/:wordId",
    gloss: "هرچه دربارهٔ یک واژه می‌دانیم",
    label: "واژه",
    title: "واژه",
    purpose: "هرچه دربارهٔ یک واژه می‌دانیم: چطور خوانده می‌شود، چند بار آمده و در کدام سطرها.",
    invitation: "در جست‌وجو روی یک واژه بزنید.",
    inNavigation: false,
    task: "۷.۳",
  },
  {
    path: "/build",
    gloss: "از یک واژه، واژه‌های تازه",
    label: "ساختن",
    title: "ساخت واژه",
    purpose:
      "یک واژه بنویسید و ببینید چه واژه‌هایی از آن ساخته می‌شود، و هر کدام چطور.",
    invitation: "یک واژه بنویسید، مثلاً «رفتن».",
    inNavigation: true,
    task: "۷.۴",
  },
  {
    path: "/compound",
    gloss: "دو واژه، یک واژهٔ تازه",
    label: "چسباندن",
    title: "واژه‌های ترکیبی",
    purpose:
      "یک واژه بنویسید و ببینید دستور زبان با آن چه ترکیب‌هایی می‌سازد، و کدام‌یک را کسی واقعاً به کار برده است.",
    invitation: "یک واژه بنویسید، مثلاً «دل».",
    inNavigation: true,
    task: "۲.۳",
  },
  {
    path: "/affixes",
    gloss: "از معنا به وند",
    label: "وندها",
    title: "وند از روی معنا",
    purpose: "از معنا شروع کنید و وندش را پیدا کنید. مثلاً: کدام وند معنای «جا» می‌دهد؟",
    invitation: "یک معنا را انتخاب کنید.",
    inNavigation: true,
    task: "۷.۵",
  },
  {
    path: "/explain",
    gloss: "این واژه از چه ساخته شده؟",
    label: "شکافتن",
    title: "شکافتن واژه",
    purpose:
      "یک واژه بنویسید و ببینید از چه ساخته شده و کدام دستورها آن را می‌سازند.",
    invitation: "یک واژه بنویسید تا ببینید از چه ساخته شده.",
    inNavigation: true,
    task: "۷.۶",
  },
  {
    path: "/rules",
    gloss: "دستورهای واژه‌سازی",
    label: "دستورها",
    title: "دستورهای واژه‌سازی",
    purpose: "همهٔ دستورها با نمونه‌هایشان، و اینکه از واژه‌هایی که هر دستور می‌سازد چندتا در پیکره آمده است.",
    invitation: "فهرست دستورها را ببینید.",
    inNavigation: true,
    task: "۷.۷",
  },
  {
    path: "/bank",
    gloss: "همهٔ واژه‌ها در گروه‌هایشان",
    label: "بانک واژه",
    title: "بانک واژه",
    purpose:
      "همهٔ واژه‌هایی که زبان‌شناس گرد آورده، در گروه‌هایی که خودش ساخته و با نام‌هایی که خودش گذاشته. کنار هر کارواژه، پیشین‌کاربن و کنون‌کاربنش را هم می‌بینید.",
    invitation: "واژه‌ای بنویسید، به خط فارسی یا به به‌نویسی، یا گروهی را انتخاب کنید.",
    inNavigation: true,
    task: "۹.۱۴",
  },
  {
    path: "/texts",
    gloss: "هر متن، واژه به واژه",
    label: "خواندن",
    title: "خواندن متن",
    purpose:
      "هر متن پیکره را، شعر یا نثر، واژه به واژه بخوانید: به خط فارسی و به بهنویس. روی هر واژه بزنید تا خوانش‌هایش را ببینید.",
    invitation: "نام نویسنده، کتاب یا عنوان را بنویسید، مثلاً «گلستان دیباچه».",
    inNavigation: true,
    task: "۹.۱۵",
  },
  {
    path: "/questions",
    gloss: "آنچه هنوز نمی‌دانیم",
    label: "پرسش‌ها",
    title: "پرسش‌هایی برای زبان‌شناس",
    purpose:
      "این بخش برای زبان‌شناس است: پرسش‌هایی که پاسخشان گرهی از کار برنامه باز می‌کند.",
    invitation: "هنوز پرسشی نیست.",
    inNavigation: true,
    task: "۹.۱۱",
  },
  {
    path: "/corpus",
    gloss: "متن‌هایی که خوانده‌ایم",
    label: "پیکره",
    title: "پیکره",
    purpose: "پیکره از کجا آمده، چه نسخه‌هایی دارد، چقدر بزرگ است و چه اندازه از آن را می‌توانیم بخوانیم.",
    invitation: "نسخه‌های پیکره را ببینید.",
    inNavigation: true,
    task: "۷.۸",
  },
];

export const NAVIGATION = SCREENS.filter((screen) => screen.inNavigation);
