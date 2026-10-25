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
      "در اینجا می‌توانید واژه‌ها را بر اساس وندها، گونه یا بسامد جست‌وجو کنید.",
    invitation: "الگویی بنویسید، مثلاً واژه‌هایی که به «نا» ختم می‌شوند.",
    inNavigation: true,
    task: "۷.۲",
  },
  {
    path: "/word/:wordId",
    gloss: "هرچه دربارهٔ یک واژه می‌دانیم",
    label: "واژه",
    title: "واژه",
    purpose: "هرچه دربارهٔ یک واژه می‌دانیم: خوانش‌ها، شواهد و شاهدمثال‌ها.",
    invitation: "از فهرست جست‌وجو یک واژه را برگزینید.",
    inNavigation: false,
    task: "۷.۳",
  },
  {
    path: "/build",
    gloss: "از یک واژه، واژه‌های تازه",
    label: "ساخت",
    title: "ساخت واژه",
    purpose: "از یک واژه، هرچه دستور زبان می‌تواند بسازد — با راه ساختش.",
    invitation: "واژه‌ای بنویسید. برای نمونه: رفتن.",
    inNavigation: true,
    task: "۷.۴",
  },
  {
    path: "/compound",
    gloss: "دو واژه، یک واژهٔ تازه",
    label: "ترکیب",
    title: "واژه‌های ترکیبی",
    purpose:
      "از یک واژه، همهٔ ترکیب‌هایی که دستور زبان می‌سازد — و اینکه کدام‌یک را کسی به کار برده است.",
    invitation: "واژه‌ای بنویسید. برای نمونه: دل.",
    inNavigation: true,
    task: "۲.۳",
  },
  {
    path: "/affixes",
    gloss: "از معنا به وند",
    label: "وندها",
    title: "وندها بر پایهٔ معنا",
    purpose: "از معنا آغاز کنید و به وند برسید. برای نمونه: کدام وند معنای «جا» می‌دهد؟",
    invitation: "یک معنا را برگزینید.",
    inNavigation: true,
    task: "۷.۵",
  },
  {
    path: "/explain",
    gloss: "این واژه از چه ساخته شده؟",
    label: "تحلیل",
    title: "تحلیل ساخت",
    purpose:
      "یک واژه را وارد کنید تا ببینید از چه ساخته شده و کدام دستورها آن را می‌سازند.",
    invitation: "واژه‌ای بنویسید تا ساختش شکافته شود.",
    inNavigation: true,
    task: "۷.۶",
  },
  {
    path: "/rules",
    gloss: "دستورهای واژه‌سازی",
    label: "دستورها",
    title: "دستورهای واژه‌سازی",
    purpose: "همهٔ دستورها، با نمونه‌ها و زایایی سنجیده‌شده در پیکره.",
    invitation: "فهرست دستورها را مرور کنید.",
    inNavigation: true,
    task: "۷.۷",
  },
  {
    path: "/questions",
    gloss: "آنچه هنوز نمی‌دانیم",
    label: "پرسش‌ها",
    title: "پرسش‌ها از زبان‌شناس",
    purpose:
      "این بخش برای زبان‌شناس طراحی شده است: پرسش‌هایی که با پاسخ آنها می‌توان گره‌های فنی سیستم را باز کرد.",
    invitation: "پرسشی ثبت نشده است.",
    inNavigation: true,
    task: "۹.۱۱",
  },
  {
    path: "/corpus",
    gloss: "متن‌هایی که خوانده‌ایم",
    label: "پیکره",
    title: "پیکره",
    purpose: "سرچشمه‌ها، نسخه‌ها، اندازه‌ها و اینکه چقدر از پیکره را می‌توانیم بخوانیم.",
    invitation: "نسخه‌های پیکره را ببینید.",
    inNavigation: true,
    task: "۷.۸",
  },
];

export const NAVIGATION = SCREENS.filter((screen) => screen.inNavigation);
