output "certificate_pem" {
  value = acme_certificate.certificate.certificate_pem
}

output "certificate_private_key_pem" {
  value = acme_certificate.certificate.private_key_pem
}
