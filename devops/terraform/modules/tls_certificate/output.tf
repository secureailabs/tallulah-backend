output "certificate_pfx" {
  value = acme_certificate.certificates.certificate_p12
}
