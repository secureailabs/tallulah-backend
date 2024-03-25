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
  rsa_bits  = 4096
}

resource "acme_registration" "registration" {
  account_key_pem = tls_private_key.private_key.private_key_pem
  email_address   = "engineering@arrayinsights.com"
}

resource "acme_certificate" "certificates" {
  account_key_pem          = acme_registration.registration.account_key_pem
  common_name              = var.host_name
  certificate_p12_password = var.ssl_certificate_password

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
