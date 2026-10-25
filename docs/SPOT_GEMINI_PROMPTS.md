# מצא את ההבדלים: פרומפטים לג'מיני (גרסה 2)

**כבר עובד:** המשחק באתר ("הבדלים" בחדר הגדולים). את הסצנות הראשונות אני מייצר בעצמי. בג'מיני אפשר להוסיף סצנות חדשות מתי שרוצים, וכל אחת הופכת לשלושה פאזלים (3, 5 ו־7 הבדלים).

**מה עושים:** מדביקים בג'מיני את **התבנית** ואחריה את **שורת הסצנה**, בתוך הודעה אחת. מכל סצנה צריך רק **תמונה אחת**. את ההבדלים אני מחביא בקוד.

## למה הכללים

- **חוקי:**
  - רק דמויות מקוריות.
  - בלי שמות של סרטים, אולפנים או דמויות מוכרות (לא "כמו אלזה", לא "בסגנון דיסני").
  - בלי לוגואים, בלי סמלים של קבוצות ספורט ובלי מותגים.
  - מותר לבקש "סגנון סרט מצויר קלאסי". אסור להעתיק דמות מסוימת.
- **הרבה חפצים נפרדים, עם רקע פשוט ביניהם:** כך אפשר למחוק או לצבוע חפץ בלי לקלקל את מה שסביבו.
- **בלי טקסט, אותיות ומספרים:** אותיות יוצאות מעוותות ויוצרות "הבדלים" שאף אחד לא סימן.
- **4:3 לרוחב:** מתאים גם לשתי תמונות אחת מעל השנייה בטלפון וגם אחת ליד השנייה בטאבלט.

## אחרי שמייצרים

1. בוחרים את התמונה עם הכי הרבה חפצים ברורים.
2. מורידים אותה בגודל מלא (PNG).
3. נותנים שם במספר הבא שפנוי: הסצנות שלי הן 00 עד 10, אז שלך מתחילות ב־`11.png`.
4. מעלים לגיטהאב, לתיקייה `assets/spot/raw/` בענף `main`: **Add file**, ואז **Upload files**. אפשר גם לשלוח לי כאן.

את סימן המים של ג'מיני בפינה אני חותך.

---

## התבנית (מדביקים לפני כל סצנה)

```
Children's picture-book illustration in a classic animated-film look: bright cheerful colors, clean bold dark outlines, flat colors with soft simple shading.
Only ORIGINAL characters: not based on any existing movie, TV show, game, toy or brand; no logos, no team badges, no trademarks.
Landscape 4:3. No text, no letters, no numbers, no signs with writing, no watermark, no signature, no border.
ONE continuous scene with a real background (sky, grass, water, a room), not a sheet of separate stickers on white.
A wide, evenly lit scene, sharp everywhere (no blur, no depth of field, no film grain, no fine noisy texture).
Fill the whole picture, edge to edge, with many separate, clearly drawn objects of different colors and sizes,
spread evenly (not crowded in the middle), each one standing on its own with plain simple background between them.
Lots of small countable details on the objects (windows, buttons, spots, stripes, petals, stars).
Scene:
```

## סצנות (שורה אחת לכל תמונה, מיד אחרי התבנית)

### אגדות וסרטים
- **טירת אגדות:** `A fairy-tale castle on a green hill: a princess in a pink gown waving from a balcony, a brave little knight with a shield, a friendly small green dragon, a white horse, a pumpkin carriage, a rainbow, three flags on the towers, a wishing well, apple trees, butterflies, a sun and two clouds.`
- **ספינת פיראטים:** `A pirate adventure: a wooden pirate ship with striped sails, a friendly pirate kid with a hat, a parrot, a small island with one palm tree, an open treasure chest with coins and jewels, a treasure map on the sand, a telescope, a barrel, a cannon with cannonballs, a whale spouting water, seagulls, a sun.`
- **ממלכת בנות הים:** `An underwater kingdom: a smiling mermaid with a purple tail, a shell palace with round windows, a seahorse, colorful fish, a sea turtle, an octopus, a treasure chest, coral, seaweed, pearls in an open shell, a starfish, bubbles.`
- **יער קסום:** `A magic forest: a tiny fairy with sparkly wings, a mushroom house with a round door and windows, a friendly owl on a branch, a fox, two rabbits, a deer, a stream with stepping stones, glowing flowers, a rainbow, fireflies, a moon and stars.`
- **גיבורי על:** `A cheerful superhero city: two kid superheroes with capes flying (original costumes, no emblems), colorful buildings with many windows, a rescued kitten on a roof, a fire truck, a hot-air balloon, a clock tower with no numbers, a park with trees, a bus, birds, clouds.`

### ספורט
- **כדורגל:** `A kids' football (soccer) match on a sunny pitch: kids in red shirts and kids in blue shirts (plain shirts, no badges, no numbers), a ball, two goals with nets, a goalkeeper jumping, a referee with a whistle, corner flags, a bench with water bottles, a happy dog running, spectators waving flags with plain colors, a sun.`
- **יום ספורט:** `A school sports day: kids running a race with a finish ribbon, a basketball hoop with a ball, a jump rope, a tennis net with rackets, a podium with three medals, cones, a trophy, a water cooler, balloons, a big tree, a sun and clouds.`
- **בריכה:** `A swimming pool day: kids swimming with goggles, an inflatable duck ring, a slide into the pool, a diving board, a lifeguard chair with an umbrella, beach balls, towels on deck chairs, a palm tree, ice-cream, flip-flops, a sun.`

### טבע ופרפרים
- **גן פרפרים:** `A butterfly garden: many butterflies in different colors and patterns, big flowers (sunflowers, tulips, daisies), a ladybug on a leaf, a snail, a bee, a little girl with a butterfly net, a birdhouse, a watering can, a small pond with a frog, a rainbow, a sun.`
- **חווה:** `A farm: a red barn with white windows, a spotted cow, a pink pig, three chickens, a green tractor, a haystack, a windmill, a wooden fence, an apple tree, a scarecrow with a hat, a duck pond, a sun and two clouds.`
- **ג'ונגל:** `A jungle: a monkey on a vine, a red parrot, a toucan, a friendly tiger, a baby elephant, a waterfall, giant flowers, butterflies, a green snake on a branch, a frog on a big leaf, palm trees, a sun.`

### ילדים במקומות מוכרים
- **מסיבת יום הולדת:** `A kids' birthday party in a garden: a big cake with candles, balloons in many colors, a table with cupcakes and juice, wrapped presents with bows, party hats, a piñata, kids dancing, a puppy, garlands of little flags, a sun.`
- **גן שעשועים:** `A playground: a slide, swings, a sandbox with toys, a seesaw, a kite in the sky, kids playing with a ball, a bench, a tree with two birds, an ice-cream stand, flowers, a sun and clouds.`
- **כיתה:** `A happy classroom: kids at colorful desks, a teacher at a board with drawings (no writing), a globe, a bookshelf with colorful books (no titles), a fish tank, plants on the window sill, a clock with no numbers, backpacks, paintings on the wall, a ball.`
- **חוף:** `A sunny beach: a big smiling sun, seagulls, a sailboat, a striped lighthouse, beach umbrellas, a sandcastle with a flag, a bucket and spade, a crab, a starfish, a beach ball, a palm tree, an ice-cream cart, a surfboard.`

---

## אם תמונה לא יצאה טוב

- **יצא טקסט או אותיות:** מוסיפים בסוף את המשפט `Absolutely no text or letters anywhere.`
- **יצא "דף מדבקות" על רקע לבן במקום סצנה:** מוסיפים `One continuous scene with a full background.`
- **דמות דומה מדי לדמות מוכרת:** מבקשים מחדש עם `Make the characters clearly original, with different colors and outfits.`
- **הכול צפוף באמצע:** מוסיפים `Spread the objects across the whole width and height.`
