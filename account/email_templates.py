GLOWMI_LOGO_URL = "https://glowmi-net.vercel.app/logo.png"

LOGO_HEADER = f'<img src="{GLOWMI_LOGO_URL}" width="48" height="48" alt="Glowmi" style="display:block;margin:0 auto;"/>'
LOGO_CARD = f'<img src="{GLOWMI_LOGO_URL}" width="32" height="32" alt="Glowmi" style="display:block;margin:0 auto;"/>'
LOGO_FOOTER = f'<img src="{GLOWMI_LOGO_URL}" width="36" height="36" alt="Glowmi" style="display:block;margin:0 auto;"/>'


def get_welcome_email_en(full_name, email, phone, membership_id, circle_id, year):
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Welcome to Glowmi Circle</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:20px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">

<!-- Header Logo -->
<tr><td align="center" style="padding:40px 40px 10px;">
<table cellpadding="0" cellspacing="0"><tr>
<td align="center" style="font-size:22px;letter-spacing:8px;color:#2c2c2c;font-weight:300;">GLOWMI</td>
</tr><tr>
<td align="center" style="font-size:11px;letter-spacing:2px;color:#888;padding-top:4px;">The Essence of Timeless Glow</td>
</tr></table>
</td></tr>

<!-- Welcome + Card Section -->
<tr><td style="padding:0 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td valign="top" width="55%" style="padding-right:20px;">
<h1 style="font-size:28px;font-weight:700;color:#1a1a1a;margin:0 0 20px;line-height:1.2;">Welcome to<br>Glowmi Circle</h1>
<p style="font-size:14px;color:#444;margin:0 0 12px;">Hello {full_name},</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">Thank you for joining Glowmi Circle.</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">You are now part of a community devoted to intelligent skincare, refined rituals, and timeless glow.</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">Your welcome privilege has been applied.</p>
<p style="font-size:14px;color:#444;margin:0 0 0;">We look forward to supporting your skin's resilience — beautifully and intentionally.</p>
</td>
<td valign="top" width="45%">
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e0e0e0;border-radius:12px;padding:24px;text-align:center;">
<tr><td align="center" style="padding-bottom:4px;">{LOGO_CARD}</td></tr>
<tr><td align="center" style="font-size:11px;letter-spacing:4px;color:#2c2c2c;padding:4px 0 16px;">GLOWMI CIRCLE</td></tr>
<tr><td align="center" style="font-size:10px;letter-spacing:3px;color:#888;border-top:1px solid #eee;padding-top:14px;">FOUNDING MEMBER</td></tr>
<tr><td align="center" style="font-size:28px;font-weight:700;color:#1a1a1a;padding:12px 0;letter-spacing:2px;">{circle_id}</td></tr>
<tr><td align="center" style="font-size:11px;color:#999;border-top:1px solid #eee;padding-top:12px;">Circle Identity</td></tr>
<tr><td align="center" style="font-size:11px;color:#999;padding-top:4px;">Member Since {year}</td></tr>
</table>
</td>
</tr></table>
</td></tr>

<!-- Membership Details -->
<tr><td style="padding:40px 40px 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #eee;padding-top:30px;">
<tr><td>
<table cellpadding="0" cellspacing="0" style="margin-bottom:20px;"><tr>
<td style="width:28px;height:28px;border:1px solid #ccc;border-radius:50%;text-align:center;vertical-align:middle;overflow:hidden;"><div style="width:6px;height:6px;border:1.5px solid #555;border-radius:50%;margin:3px auto 1px;"></div><div style="width:14px;height:6px;border:1.5px solid #555;border-bottom:none;border-radius:6px 6px 0 0;margin:0 auto;"></div></td>
<td style="padding-left:10px;font-size:16px;font-weight:600;color:#1a1a1a;">Your Membership Details</td>
</tr></table>
<table width="100%" cellpadding="12" cellspacing="0" style="border:1px solid #eee;border-radius:8px;">
<tr style="background:#fafafa;">
<td style="font-size:9px;letter-spacing:2px;color:#888;border-right:1px solid #eee;width:25%;">MEMBER NAME</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;border-right:1px solid #eee;width:25%;">EMAIL ADDRESS</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;border-right:1px solid #eee;width:25%;">MOBILE NUMBER</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;width:25%;">CIRCLE ID</td>
</tr>
<tr>
<td style="font-size:13px;color:#333;border-right:1px solid #eee;">{full_name}</td>
<td style="font-size:13px;color:#333;border-right:1px solid #eee;">{email}</td>
<td style="font-size:13px;color:#333;border-right:1px solid #eee;">{phone}</td>
<td style="font-size:13px;color:#333;">{circle_id}</td>
</tr>
</table>
</td></tr>
</table>
</td></tr>

<!-- Benefits Section -->
<tr><td style="padding:40px;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #eee;padding-top:30px;">
<tr><td>
<table cellpadding="0" cellspacing="0" style="margin-bottom:24px;"><tr>
<td style="font-size:18px;color:#2c2c2c;padding-right:8px;">&#9734;</td>
<td style="font-size:16px;font-weight:600;color:#1a1a1a;">Your Founding Member Benefits</td>
</tr></table>

<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#8853;</td>
<td style="padding-left:12px;"><b style="font-size:14px;color:#1a1a1a;">Priority Access</b><br><span style="font-size:13px;color:#666;">Be the first to discover new product launches and innovations.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9744;</td>
<td style="padding-left:12px;"><b style="font-size:14px;color:#1a1a1a;">Early Invitations</b><br><span style="font-size:13px;color:#666;">Receive early access to exclusive events and experiences.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9734;</td>
<td style="padding-left:12px;"><b style="font-size:14px;color:#1a1a1a;">Exclusive Member Rewards</b><br><span style="font-size:13px;color:#666;">Enjoy special offers, rewards, and members-only privileges.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#10023;</td>
<td style="padding-left:12px;"><b style="font-size:14px;color:#1a1a1a;">Personalized Skincare</b><br><span style="font-size:13px;color:#666;">Experience skincare guidance curated for your unique skin.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9671;</td>
<td style="padding-left:12px;"><b style="font-size:14px;color:#1a1a1a;">Lifetime Founding Member Privileges</b><br><span style="font-size:13px;color:#666;">Enjoy exclusive benefits as a valued founding member.</span></td>
</tr></table>
</td></tr>
</table>

</td></tr>
</table>
</td></tr>

<!-- Born in Saudi Arabia -->
<tr><td align="center" style="padding:10px 40px 30px;">
<table cellpadding="0" cellspacing="0"><tr>
<td align="center" style="padding-right:12px;">{LOGO_FOOTER}</td>
<td><span style="font-size:13px;color:#555;">Born in Saudi Arabia.</span><br><span style="font-size:13px;color:#555;">Created for the World.</span></td>
</tr></table>
</td></tr>

<!-- Footer -->
<tr><td style="background:#fafafa;padding:24px 40px;text-align:center;border-top:1px solid #eee;">
<p style="font-size:12px;color:#888;margin:0 0 6px;">If you have any questions, our team is always here to assist you.</p>
<p style="font-size:12px;color:#888;margin:0 0 6px;">Thank you for being part of Glowmi Circle.</p>
<p style="font-size:11px;color:#aaa;margin:12px 0 0;">&copy; {year} Glowmi. All Rights Reserved.</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def get_welcome_email_ar(full_name, email, phone, membership_id, circle_id, year):
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>مرحبًا بك في Glowmi Circle</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:20px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">

<!-- Header Logo -->
<tr><td align="center" style="padding:40px 40px 10px;">
<table cellpadding="0" cellspacing="0"><tr>
<td align="center" style="font-size:22px;letter-spacing:8px;color:#2c2c2c;font-weight:300;">GLOWMI</td>
</tr><tr>
<td align="center" style="font-size:11px;letter-spacing:2px;color:#888;padding-top:4px;">جوهر التوهج الخالد</td>
</tr></table>
</td></tr>

<!-- Welcome + Card Section -->
<tr><td style="padding:0 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td valign="top" width="55%" style="padding-left:20px;">
<h1 style="font-size:28px;font-weight:700;color:#1a1a1a;margin:0 0 20px;line-height:1.2;">مرحبًا بك في<br>Glowmi Circle</h1>
<p style="font-size:14px;color:#444;margin:0 0 12px;">مرحبًا {full_name}،</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">شكرًا لانضمامك إلى Glowmi Circle.</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">أنت الآن جزء من مجتمع مكرس للعناية الذكية بالبشرة والطقوس الراقية والتوهج الخالد.</p>
<p style="font-size:14px;color:#444;margin:0 0 12px;">تم تفعيل امتياز الترحيب الخاص بك.</p>
<p style="font-size:14px;color:#444;margin:0 0 0;">نتطلع لدعم مرونة بشرتك — بجمال وعناية.</p>
</td>
<td valign="top" width="45%">
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e0e0e0;border-radius:12px;padding:24px;text-align:center;">
<tr><td align="center" style="padding-bottom:4px;">{LOGO_CARD}</td></tr>
<tr><td align="center" style="font-size:11px;letter-spacing:4px;color:#2c2c2c;padding:4px 0 16px;">GLOWMI CIRCLE</td></tr>
<tr><td align="center" style="font-size:10px;letter-spacing:3px;color:#888;border-top:1px solid #eee;padding-top:14px;">عضو مؤسس</td></tr>
<tr><td align="center" style="font-size:28px;font-weight:700;color:#1a1a1a;padding:12px 0;letter-spacing:2px;">{circle_id}</td></tr>
<tr><td align="center" style="font-size:11px;color:#999;border-top:1px solid #eee;padding-top:12px;">هوية الدائرة</td></tr>
<tr><td align="center" style="font-size:11px;color:#999;padding-top:4px;">عضو منذ {year}</td></tr>
</table>
</td>
</tr></table>
</td></tr>

<!-- Membership Details -->
<tr><td style="padding:40px 40px 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #eee;padding-top:30px;">
<tr><td>
<table cellpadding="0" cellspacing="0" style="margin-bottom:20px;"><tr>
<td style="width:28px;height:28px;border:1px solid #ccc;border-radius:50%;text-align:center;vertical-align:middle;overflow:hidden;"><div style="width:6px;height:6px;border:1.5px solid #555;border-radius:50%;margin:3px auto 1px;"></div><div style="width:14px;height:6px;border:1.5px solid #555;border-bottom:none;border-radius:6px 6px 0 0;margin:0 auto;"></div></td>
<td style="padding-right:10px;font-size:16px;font-weight:600;color:#1a1a1a;">تفاصيل عضويتك</td>
</tr></table>
<table width="100%" cellpadding="12" cellspacing="0" style="border:1px solid #eee;border-radius:8px;">
<tr style="background:#fafafa;">
<td style="font-size:9px;letter-spacing:2px;color:#888;border-left:1px solid #eee;width:25%;">اسم العضو</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;border-left:1px solid #eee;width:25%;">البريد الإلكتروني</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;border-left:1px solid #eee;width:25%;">رقم الجوال</td>
<td style="font-size:9px;letter-spacing:2px;color:#888;width:25%;">رقم الدائرة</td>
</tr>
<tr>
<td style="font-size:13px;color:#333;border-left:1px solid #eee;">{full_name}</td>
<td style="font-size:13px;color:#333;border-left:1px solid #eee;direction:ltr;">{email}</td>
<td style="font-size:13px;color:#333;border-left:1px solid #eee;direction:ltr;">{phone}</td>
<td style="font-size:13px;color:#333;">{circle_id}</td>
</tr>
</table>
</td></tr>
</table>
</td></tr>

<!-- Benefits Section -->
<tr><td style="padding:40px;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #eee;padding-top:30px;">
<tr><td>
<table cellpadding="0" cellspacing="0" style="margin-bottom:24px;"><tr>
<td style="font-size:18px;color:#2c2c2c;padding-left:8px;">&#9734;</td>
<td style="font-size:16px;font-weight:600;color:#1a1a1a;">مزايا العضو المؤسس</td>
</tr></table>

<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#8853;</td>
<td style="padding-right:12px;"><b style="font-size:14px;color:#1a1a1a;">أولوية الوصول</b><br><span style="font-size:13px;color:#666;">كن أول من يكتشف المنتجات والابتكارات الجديدة.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9744;</td>
<td style="padding-right:12px;"><b style="font-size:14px;color:#1a1a1a;">دعوات مبكرة</b><br><span style="font-size:13px;color:#666;">احصل على وصول مبكر للفعاليات والتجارب الحصرية.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9734;</td>
<td style="padding-right:12px;"><b style="font-size:14px;color:#1a1a1a;">مكافآت حصرية للأعضاء</b><br><span style="font-size:13px;color:#666;">استمتع بالعروض والمكافآت وامتيازات الأعضاء فقط.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#10023;</td>
<td style="padding-right:12px;"><b style="font-size:14px;color:#1a1a1a;">عناية مخصصة بالبشرة</b><br><span style="font-size:13px;color:#666;">تجربة إرشادات عناية بالبشرة مصممة خصيصًا لبشرتك.</span></td>
</tr></table>
</td></tr>
<tr><td style="padding:12px 0;">
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:36px;height:36px;border:1px solid #ddd;border-radius:8px;text-align:center;line-height:36px;font-size:16px;color:#555;" valign="middle">&#9671;</td>
<td style="padding-right:12px;"><b style="font-size:14px;color:#1a1a1a;">امتيازات العضو المؤسس مدى الحياة</b><br><span style="font-size:13px;color:#666;">استمتع بمزايا حصرية كعضو مؤسس مميز.</span></td>
</tr></table>
</td></tr>
</table>

</td></tr>
</table>
</td></tr>

<!-- Born in Saudi Arabia -->
<tr><td align="center" style="padding:10px 40px 30px;">
<table cellpadding="0" cellspacing="0"><tr>
<td align="center" style="padding-left:12px;">{LOGO_FOOTER}</td>
<td><span style="font-size:13px;color:#555;">ولدت في المملكة العربية السعودية.</span><br><span style="font-size:13px;color:#555;">صُنعت للعالم.</span></td>
</tr></table>
</td></tr>

<!-- Footer -->
<tr><td style="background:#fafafa;padding:24px 40px;text-align:center;border-top:1px solid #eee;">
<p style="font-size:12px;color:#888;margin:0 0 6px;">إذا كان لديك أي أسئلة، فريقنا دائمًا هنا لمساعدتك.</p>
<p style="font-size:12px;color:#888;margin:0 0 6px;">شكرًا لكونك جزءًا من Glowmi Circle.</p>
<p style="font-size:11px;color:#aaa;margin:12px 0 0;">&copy; {year} Glowmi. جميع الحقوق محفوظة.</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
