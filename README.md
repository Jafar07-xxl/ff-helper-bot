# FF Helper Telegram Bot

FF Helper is a Python bot for Free Fire fans. It supports Russian and Tajik,
shows buttons for Free Fire diamonds, Telegram Stars, and Telegram Premium,
and lets customers submit orders for manual payment review.

The bot uses Python's built-in libraries. No package installation or manual
code editing is needed to use it.

## What customers can do

1. Send `/start` and choose **🇷🇺 Русский** or **🇹🇯 Тоҷикӣ**.
2. Tap a product category:
   - Russian: **💎 Купить алмазы FF**, **⭐ Купить Telegram Stars**, or
     **👑 Купить Telegram Premium**
   - Tajik: **💎 Харидани алмосҳои FF**, **⭐ Харидани Telegram Stars**, or
     **👑 Харидани Telegram Premium**
3. Choose a product:
   - 100 diamonds — 10 TJS
   - 300 diamonds — 29 TJS
   - 500 diamonds — 48 TJS
   - 1,000 diamonds — 98 TJS
   - Weekly voucher — 18 TJS
   - Monthly voucher — 78 TJS
   - 50 Telegram Stars — 15 TJS
   - 100 Telegram Stars — 28 TJS
   - 250 Telegram Stars — 65 TJS
   - 500 Telegram Stars — 125 TJS
   - Telegram Premium: 1 month — 45 TJS
   - Telegram Premium: 3 months — 130 TJS
   - Telegram Premium: 12 months — 400 TJS
4. Enter the Free Fire UID, then confirm it or choose to change it.
5. Check the order summary and choose **Alif** or **Dushanbe City**.
6. Follow the payment instructions and send a receipt photo in the private chat.

The receipt and order details are sent to the administrator for review. Uploading
a receipt never marks an order as paid. The administrator must check that the
money arrived and press **Approve Payment** or **Reject Payment**.

After approval, the customer is told that payment was checked and the order is
being processed. The bot does not say the product was delivered.
An order without a receipt is automatically cancelled after 20 minutes.
Orders with a submitted receipt stay open for manual administrator review.

## Configure the administrator and payment details securely

These settings are stored in Replit Secrets:

- `ADMIN_TELEGRAM_ID` — the administrator's numeric Telegram user ID, not an
  `@username`. To find it, open a private chat with this bot and send `/id`.
  Copy the number into this Secret.
- `ALIF_PAYMENT_DETAILS` — the Alif payment instructions customers should see.
- `DUSHANBE_CITY_PAYMENT_DETAILS` — the Dushanbe City payment instructions
  customers should see.
- `TELEGRAM_BOT_TOKEN` — the bot's existing BotFather token.

The administrator ID and payment details were collected using Replit's secure
Secrets form. To change them later:

1. Open **Secrets** in the Replit project.
2. Update the value for the matching key above.
3. Save and restart **FF Helper Bot** from Workflows.

The payment details are private in Replit Secrets, but the bot displays the
matching instructions to customers when they choose that payment method. Enter
only information customers should use to send a payment. Never enter a PIN,
password, CVV, bank login, or one-time verification code.

Before accepting orders, the administrator should open a private chat with the
bot, send `/start`, and choose a language. This lets Telegram deliver order
receipts and review notices to the administrator.

## Start and test the bot

1. Open **Workflows** in Replit.
2. Select **FF Helper Bot** and tap **Run** or **Start**.
3. In Telegram, open the bot's private chat and send `/start`.
4. Test Russian: tap **🇷🇺 Русский**. Check that the main menu contains only
   the three purchase-category buttons. Open each category and check its product
   prices. Try entering and confirming a UID, reviewing the summary, and opening
   the payment-method menu.
5. Send `/start` again to switch to **🇹🇯 Тоҷикӣ**. Check the three Tajik
   purchase-category buttons and repeat the product and order checks.
6. To test approval safely, submit a test order with a receipt only after
   checking the payment flow. The administrator's account receives the receipt
   and order summary with the review buttons.

Do not start two copies of the bot at once; Telegram allows only one copy to
check for new messages for this bot.

You can also start the bot from Replit Shell with:

```sh
python3 bots/ff-helper/bot.py
```

## Existing features and safety

- Game News, Player Stats, and Help handlers remain in the code but are not
  displayed in the main menu.
- Shop orders and language choices are saved in a local SQLite database.
  The database is ignored by Git. Receipt images are sent to Telegram's admin
  chat; they are not downloaded into the project.
- Approve/reject controls work only for the numeric administrator ID in
  `ADMIN_TELEGRAM_ID`. The order must also still be awaiting review.
- Orders that have not received a receipt expire 20 minutes after creation.
- Prices are listed above. Ask Replit Agent to change the products or prices;
  you do not need to edit Python code.

## If the bot does not start or reply

- Check that **FF Helper Bot** is running in Workflows.
- Check that each required Secret is present and spelled exactly as shown above.
- `ADMIN_TELEGRAM_ID` must contain digits only. Run `/id` in the administrator's
  private chat to check the correct number.
- The administrator must open the bot in Telegram before the bot can send them
  order receipts.
- If you change a Secret, restart the workflow.
