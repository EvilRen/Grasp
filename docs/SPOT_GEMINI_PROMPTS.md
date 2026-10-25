# מצא את ההבדלים: פרומפטים לג'מיני

**כבר עובד:** המשחק באתר ("הבדלים" בחדר הגדולים) עם תמונת דוגמה אחת של חוף. כשיגיעו 10 התמונות שלך, אחביא בהן את ההבדלים ואוסיף אותן.

**מה עושים:** לכל אחת מ־10 הסצנות מדביקים בג'מיני את **התבנית** ואחריה את **שורת הסצנה**, בתוך הודעה אחת. מכל סצנה צריך רק **תמונה אחת**. את ההבדלים אני מחביא בקוד: מוחק, צובע, מזיז ומוסיף חפצים. כך כל הבדל יושב במקום מדויק, ומכל תמונה יוצאות שלוש רמות: 3, 5 ו־7 הבדלים.

**למה הכללים בתבנית:**
- **הרבה חפצים נפרדים עם רקע פשוט ביניהם:** כך אפשר למחוק או לצבוע חפץ בלי לקלקל את מה שסביבו.
- **בלי טקסט, אותיות ומספרים:** אותיות יוצאות מעוותות ויוצרות "הבדלים" שאף אחד לא סימן.
- **4:3 לרוחב:** מתאים גם לשתי תמונות אחת מעל השנייה בטלפון וגם אחת ליד השנייה בטאבלט.
- **בלי טשטוש ובלי טקסטורה דקה:** תיקון באזור מטושטש או מגורען נראה מלוכלך.

**אחרי שמייצרים:**
1. בוחרים את התמונה עם הכי הרבה חפצים ברורים.
2. מורידים אותה בגודל מלא (PNG).
3. קוראים לקבצים לפי הסדר: `01.png` עד `10.png`.
4. מעלים את כולם לגיטהאב, בתיקייה `assets/spot/raw/` בענף `main`: **Add file**, ואז **Upload files**.

את סימן המים של ג'מיני בפינה אני חותך.

---

## התבנית (מדביקים לפני כל סצנה)

```
Children's picture-book illustration, bright cheerful colors, clean bold dark outlines, flat colors with soft simple shading.
Landscape 4:3. No text, no letters, no numbers, no signs with writing, no watermark, no signature, no border.
A wide, evenly lit scene, sharp everywhere (no blur, no depth of field, no film grain, no fine noisy texture).
Fill the whole picture, edge to edge, with many separate, clearly drawn objects of different colors and sizes,
spread evenly (not crowded in the middle), each one standing on its own with plain simple background between them.
Lots of small countable details on the objects (windows, buttons, spots, stripes, petals, apples, stars).
Scene:
```

## 10 הסצנות (שורה אחת לכל תמונה, מיד אחרי התבנית)

1. **חוף:** `A sunny beach: a big smiling sun, three seagulls, a sailboat on the sea, a striped lighthouse, a striped beach umbrella, a sandcastle with a little flag, a bucket and spade, a red crab, an orange starfish, a beach ball, a palm tree with coconuts, an ice-cream cart, a surfboard, a few shells.`
2. **חווה:** `A farm: a red barn with white windows, a spotted cow, a pink pig, three chickens, a green tractor, a haystack, a windmill, a wooden fence, an apple tree full of red apples, a scarecrow with a hat, a small duck pond with two ducks, a sun and two clouds.`
3. **חלל:** `Outer space: a red-and-white rocket, a ringed planet, a moon with craters, a smiling astronaut floating, a friendly alien in a flying saucer, a comet, a satellite, three small planets in different colors, a space station with round windows, many big simple stars.`
4. **מתחת לים:** `Under the sea: a colorful coral reef, four different bright fish, an octopus, a sea turtle, an open treasure chest with gold coins, a seahorse, a pink jellyfish, a yellow submarine with round windows, seaweed, shells, a starfish, a few big bubbles.`
5. **ג'ונגל:** `A jungle: a monkey hanging on a vine, a red parrot, a toucan, a friendly tiger, a baby elephant, a waterfall, giant colorful flowers, three butterflies, a green snake on a branch, a frog on a big leaf, palm trees, a sun.`
6. **רחוב בעיר:** `A friendly town street: colorful houses with many windows and doors, a yellow bus, a red car, a traffic light, a bakery with a striped awning, a tree, a dog on a leash, two kids with balloons, a bicycle, a street lamp, a mailbox, clouds and birds.`
7. **מטבח:** `A cozy kitchen: a table with a bowl of fruit, a teapot and three cups, a round wall clock with no numbers, a window with curtains and a plant, a cat on a chair, shelves with colorful jars, a cake on a plate, pots and pans, a fridge with picture magnets, a striped rug.`
8. **גן שעשועים:** `A playground: a slide, swings, a sandbox with toys, a seesaw, a kite in the sky, kids playing with a ball, a bench, a tree with two birds, an ice-cream stand, flowers, a sun and clouds.`
9. **חורף:** `A snowy winter village: a snowman with a scarf, hat and buttons, little houses with lit windows and chimney smoke, a sled, pine trees with ornaments, a penguin, a red fox, a kid ice skating on a pond, wrapped gift boxes, a few big snowflakes, a moon.`
10. **עמק הדינוזאורים:** `A friendly dinosaur valley: a long-neck dinosaur, a small cute T-rex, a triceratops, a volcano with a little smoke, a nest with three spotted eggs, a flying pterodactyl, a river with stepping stones, big ferns and palm trees, mushrooms, rocks, a sun.`

---

## אם תמונה לא יצאה טוב

- **יצא טקסט או אותיות:** מוסיפים בסוף את המשפט `Absolutely no text or letters anywhere.`
- **הכול צפוף באמצע:** מוסיפים `Spread the objects across the whole width and height.`
- **יצא לאורך במקום לרוחב:** מבקשים מחדש עם `wide landscape 4:3 image`.
