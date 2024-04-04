from django.core.cache import cache
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver


@receiver([pre_save, pre_delete], sender=Company)
def company_m2m_changed(sender, instance: Company, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of Company model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the Company model.
        kwargs: Additional keyword arguments.
    """
    company_instance = Company.objects.filter(id=instance.id).first()
    if company_instance:
        m2m_ids = company_instance.items.values_list("id", flat=True)
        cache_key = hash(company_instance)
        cache.set(cache_key, list(m2m_ids))


@receiver([pre_save, pre_delete], sender=Individual)
def individual_m2m_changed(sender, instance: Individual, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of Individual model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the Individual model.
        kwargs: Additional keyword arguments.
    """
    individual_instance = Individual.objects.filter(id=instance.id).first()
    m2m_ids = {}
    if individual_instance:
        m2m_ids["cx_questions"] = list(individual_instance.cx_questions.values_list("id", flat=True))
        m2m_ids["item_conversations"] = list(individual_instance.item_conversations.values_list("id", flat=True))
        m2m_ids["item_statements"] = list(individual_instance.item_statements.values_list("id", flat=True))
        m2m_ids["items"] = list(individual_instance.items.values_list("id", flat=True))
        cache_key = hash(individual_instance)
        cache.set(cache_key, m2m_ids)


@receiver([pre_save, pre_delete], sender=CXQuestion)
def cxquestion_m2m_changed(sender, instance: CXQuestion, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of CXQuestion model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the CXQuestion model.
        kwargs: Additional keyword arguments.
    """
    cxquestion_instance = CXQuestion.objects.filter(id=instance.id).first()
    m2m_ids = {}
    if cxquestion_instance:
        m2m_ids["individual_questions"] = list(cxquestion_instance.individual_questions.values_list("id", flat=True))
        cache_key = hash(cxquestion_instance)
        cache.set(cache_key, m2m_ids)


@receiver([pre_save, pre_delete], sender=Document)
def document_m2m_changed(sender, instance: Document, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of Document model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the Document model.
        kwargs: Additional keyword arguments.
    """
    document_instance = Document.objects.filter(id=instance.id).first()
    m2m_ids = {}
    if document_instance:
        m2m_ids["legal_actions"] = list(document_instance.legal_actions.values_list("id", flat=True))
        cache_key = hash(document_instance)
        cache.set(cache_key, m2m_ids)


@receiver([pre_save, pre_delete], sender=LegalAction)
def legal_action_m2m_changed(sender, instance: LegalAction, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of LegalAction model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the LegalAction model.
        kwargs: Additional keyword arguments.
    """
    legal_action = LegalAction.objects.filter(id=instance.id).first()
    m2m_ids = {}
    if legal_action:
        m2m_ids["documents"] = list(legal_action.documents.values_list("id", flat=True))
        m2m_ids["items"] = list(legal_action.items.values_list("id", flat=True))
        cache_key = hash(legal_action)
        cache.set(cache_key, m2m_ids)


@receiver([pre_save, pre_delete], sender=Item)
def item_m2m_changed(sender, instance: Item, **kwargs) -> None:
    """
    Signal handler for changes in Many-to-Many fields of Item model.

    Args:
        sender: The sender of the signal.
        instance: The instance of the Item model.
        kwargs: Additional keyword arguments.
    """
    item_instance = Item.objects.filter(id=instance.id).first()
    m2m_ids = {}
    if item_instance:
        m2m_ids["companies"] = list(item_instance.companies.values_list("id", flat=True))
        m2m_ids["legal_actions"] = list(item_instance.legal_actions.values_list("id", flat=True))
        m2m_ids["individual_conversations"] = list(item_instance.individual_conversations.values_list("id", flat=True))
        m2m_ids["individual_statements"] = list(item_instance.individual_statements.values_list("id", flat=True))
        m2m_ids["witnesses"] = list(item_instance.witnesses.values_list("id", flat=True))
        cache_key = hash(item_instance)
        cache.set(cache_key, m2m_ids)
