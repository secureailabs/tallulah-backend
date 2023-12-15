terraform {
  required_providers {
    acme = {
      source  = "vancluever/acme"
      version = "~> 2.0"
    }
  }
}

provider "acme" {
  server_url = "https://acme-v02.api.letsencrypt.org/directory"
}

resource "tls_private_key" "private_key" {
  algorithm = "RSA"
}

resource "acme_registration" "reg" {
  account_key_pem = tls_private_key.private_key.private_key_pem
  email_address   = "engineering@arrayinsights.com"
}

resource "acme_certificate" "certificate" {
  account_key_pem = acme_registration.reg.account_key_pem
  common_name     = var.host_name

  # dns_challenge {
  #   provider = "googledomains"

  #   config = {
  #     GOOGLE_DOMAINS_ACCESS_TOKEN        = var.google_domains_token
  #     GOOGLE_DOMAINS_HTTP_TIMEOUT        = 600
  #     GOOGLE_DOMAINS_POLLING_INTERVAL    = 300
  #     GOOGLE_DOMAINS_PROPAGATION_TIMEOUT = 300
  #   }
  # }


  dns_challenge {
    provider = "godaddy"

    config = {
      GODADDY_API_KEY             = var.godaddy_api_key
      GODADDY_API_SECRET          = var.godaddy_api_secret
      GODADDY_HTTP_TIMEOUT        = 600
      GODADDY_POLLING_INTERVAL    = 300
      GODADDY_PROPAGATION_TIMEOUT = 300
      GODADDY_TTL                 = 600
    }
  }
}

resource "local_file" "certificate" {
  content    = acme_certificate.certificate.certificate_pem
  filename   = "certificate.pem"
  depends_on = [acme_certificate.certificate]
}


resource "local_file" "private_key" {
  content    = acme_certificate.certificate.private_key_pem
  filename   = "private_key.pem"
  depends_on = [acme_certificate.certificate]
}

resource "local_file" "issuer_pem" {
  content    = acme_certificate.certificate.issuer_pem
  filename   = "issuer.pem"
  depends_on = [acme_certificate.certificate]
}


resource "null_resource" "convert_to_pfx" {
  provisioner "local-exec" {
    command = "openssl pkcs12 -export -out ${var.ssl_certificate_file_path} -inkey private_key.pem -in certificate.pem -certfile issuer.pem -passout pass:${var.ssl_certificate_password}"
  }
  depends_on = [local_file.certificate]
}
