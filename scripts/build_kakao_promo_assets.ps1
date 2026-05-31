Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutputDir = Join-Path $RepoRoot "static\promo"
$PickyImage = Join-Path $RepoRoot "static\picky\picky-aha-generated.png"
$FontRegular = "C:\Windows\Fonts\malgun.ttf"
$FontBold = "C:\Windows\Fonts\malgunbd.ttf"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function U($base64) {
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($base64))
}

function New-Font($path, $size, $style) {
    $collection = New-Object System.Drawing.Text.PrivateFontCollection
    $collection.AddFontFile($path)
    return New-Object System.Drawing.Font($collection.Families[0], $size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function Draw-WrappedText($graphics, $text, $font, $brush, $x, $y, $maxWidth, $lineHeight) {
    $line = ""
    foreach ($char in $text.ToCharArray()) {
        $next = "$line$char"
        $size = $graphics.MeasureString($next, $font)
        if ($size.Width -gt $maxWidth -and $line.Length -gt 0) {
            $graphics.DrawString($line, $font, $brush, $x, $y)
            $line = "$char"
            $y += $lineHeight
        } else {
            $line = $next
        }
    }
    if ($line.Length -gt 0) {
        $graphics.DrawString($line, $font, $brush, $x, $y)
        $y += $lineHeight
    }
    return $y
}

function Draw-CenteredText($graphics, $text, $font, $brush, $x, $y, $width) {
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $graphics.DrawString($text, $font, $brush, (New-Object System.Drawing.RectangleF($x, $y, $width, 120)), $format)
}

function New-PromoImage($fileName, $width, $height, $headline, $subhead, $keyword, $footer) {
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $picky = [System.Drawing.Image]::FromFile($PickyImage)

    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $graphics.Clear([System.Drawing.Color]::FromArgb(255, 255, 248, 235))

        $yellow = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 255, 221, 51))
        $ink = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 32, 32, 32))
        $muted = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 84, 84, 84))
        $white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
        $accent = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 49, 130, 246))

        $headlineFont = New-Font $FontBold 78 ([System.Drawing.FontStyle]::Bold)
        $subheadFont = New-Font $FontRegular 38 ([System.Drawing.FontStyle]::Regular)
        $keywordFont = New-Font $FontBold 54 ([System.Drawing.FontStyle]::Bold)
        $footerFont = New-Font $FontRegular 34 ([System.Drawing.FontStyle]::Regular)

        $graphics.FillEllipse($yellow, -160, -140, 520, 520)
        $graphics.FillEllipse($accent, $width - 260, 70, 170, 170)

        $mascotWidth = [int]($width * 0.52)
        $mascotHeight = [int]($picky.Height * ($mascotWidth / $picky.Width))
        $mascotX = [int](($width - $mascotWidth) / 2)
        $mascotY = [int]($height * 0.08)
        $graphics.DrawImage($picky, $mascotX, $mascotY, $mascotWidth, $mascotHeight)

        $textTop = [int]($height * 0.48)
        Draw-CenteredText $graphics $headline $headlineFont $ink 70 $textTop ($width - 140)
        $subTop = $textTop + 130
        Draw-CenteredText $graphics $subhead $subheadFont $muted 95 $subTop ($width - 190)

        $pillWidth = [int]($width * 0.72)
        $pillHeight = 120
        $pillX = [int](($width - $pillWidth) / 2)
        $pillY = $subTop + 185
        $pillRect = New-Object System.Drawing.Rectangle($pillX, $pillY, $pillWidth, $pillHeight)
        $graphics.FillRectangle($yellow, $pillRect)
        Draw-CenteredText $graphics $keyword $keywordFont $ink $pillX ($pillY + 22) $pillWidth

        $footerY = $pillY + 170
        Draw-CenteredText $graphics $footer $footerFont $muted 80 $footerY ($width - 160)

        $out = Join-Path $OutputDir $fileName
        $bitmap.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $picky.Dispose()
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

New-PromoImage "kakao-threads-lunch.png" 1080 1350 (U "7Jik64qYIOygkOyLrCDrrZAg66i57KeAPw==") (U "7Lm07Yah7JeQ7IScIDfrsojrp4wg64iE66W066m0IOuplOuJtCDtm4Trs7QgM+qwnA==") (U "7KCQ7Ius7LaU7LKc") (U "UGlja3kg66mU64m07LaU7LKcIOyxl+u0hw==")
New-PromoImage "kakao-story-solo.png" 1080 1920 (U "7Zi867ClIOuplOuJtCDqs6Drr7wg64Gd") (U "6rCA67ON6rKMIOuoueydhOyngCDrk6Drk6DtlZjqsowg66i57J2E7KeAIO2UvO2CpOqwgCDqs6jrnbzspJjsmpQ=") (U "7Zi867Cl7LaU7LKc") (U "7Lm07Yah7JeQ7IScIFBpY2t5")
New-PromoImage "kakao-build-log.png" 1080 1350 (U "MSwwMDDrqoUg7LGM66aw7KeA") (U "7Lm07YahIOuplOuJtCDstpTsspwg67SHIFBpY2t566W8IO2CpOyasOuKlCDspJE=") (U "7ZS87YKk7LaU7LKc") (U "7I2o67O06rOgIO2UvOuTnOuwsSDso7zshLjsmpQ=")
