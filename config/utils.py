import uuid

def generate_unique_slug(model_instance, base_slug, slug_field_name):
    """Generuoja unikalų slug lauką modeliui."""
    slug = base_slug
    unique_slug = slug
    extension = 1
    ModelClass = model_instance.__class__
    max_retries = 1000

    # Tikriname, ar toks slug jau egzistuoja (išskyrus patį saveinamą objektą)
    qs_exists = ModelClass.objects.filter(**{slug_field_name: unique_slug})
    if model_instance.pk:
        qs_exists = qs_exists.exclude(pk=model_instance.pk)

    while qs_exists.exists():
        if extension > max_retries:
            unique_slug = f'{slug}-{uuid.uuid4().hex[:6]}'
            # Patikrinam dar kartą su UUID
            qs_exists = ModelClass.objects.filter(**{slug_field_name: unique_slug})
            if model_instance.pk:
                 qs_exists = qs_exists.exclude(pk=model_instance.pk)
            if qs_exists.exists():
                 # Labai reta situacija, bet apsidraudžiame
                 raise RuntimeError(f"Cannot generate unique slug for {base_slug} after {max_retries} tries.")
        else:
          unique_slug = f'{slug}-{extension}'
        extension += 1
        # Atnaujiname queryset'ą tikrinimui su nauju slug'u
        qs_exists = ModelClass.objects.filter(**{slug_field_name: unique_slug})
        if model_instance.pk:
            qs_exists = qs_exists.exclude(pk=model_instance.pk)

    return unique_slug